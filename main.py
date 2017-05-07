from asyncio import ensure_future, get_event_loop, wait_for, Queue
from aiohttp import ClientSession
from config import log, USER_AGENT, TARGET_URL, ACCEPT_HEADERS, CONCURRENCY, TIMEOUT
from biplist import writePlist
from urllib.parse import urljoin, urldefrag, urlparse, unquote
from lxml import html
from cgi import parse_header
from cssutils import getUrls, parseString

async def crawler(client, url_queue, archive):
    while True:
        url = await url_queue.get()
        try:
            log.debug(url)
            headers = ACCEPT_HEADERS
            headers['Referer'] = archive['top']
            response = await client.get(url, headers=headers)
            if response.status != 200:
                log.warn('BAD RESPONSE: {}: {}'.format(response.status, url))
            else:
                data = await response.read()
                content_type, params = parse_header(response.headers['content-type'])
                item = {
                    "WebResourceData": data,
                    "WebResourceMIMEType": content_type,
                    "WebResourceURL": url
                }
                if 'charset' in params:
                    item['WebResourceTextEncodingName'] = params['charset']
                # TODO: attempt to reproduce the way HTTP headers are stored (NSKeyedArchiver?)
                archive['items'].append(item)
                archive['seen'][url] = True
                if 'text/html' == content_type:
                    dom = html.fromstring(data)
                    patterns = ['//img/@src', '//img/@data-src', '//img/@data-src-retina', '//script/@src', "//link[@rel='stylesheet']/@href"]
                    for path in patterns:
                        for attr in dom.xpath(path):
                            log.debug("{}: {} {}".format(path, url, attr))
                            url = unquote(urljoin(url, urldefrag(attr)[0]))
                            if url not in archive['seen']:
                                archive['seen'][url] = True
                                await url_queue.put(url)
                elif 'text/css' == content_type:
                    # TODO: nested @import and better path inference
                    for attr in getUrls(parseString(data)):
                        log.debug(attr)
                        url = unquote(urljoin(url, urldefrag(attr)[0]))
                        if url not in archive['seen']:
                            archive['seen'][url] = True
                            await url_queue.put(url)
        except Exception as exc:
            log.warn('Exception {}:'.format(exc), exc_info=True)

        finally:
            url_queue.task_done()


async def scrape(client, url):
    tasks = []
    url_queue = Queue()

    archive = {
        'top': url,
        'seen': {},
        'items': []
    }
    await url_queue.put(url)

    def task_completed(future):
        exc = future.exception()
        if exc:
            log.error('Worker finished with error: {} '.format(exc), exc_info=True)

    for _ in range(CONCURRENCY):
        crawler_future = ensure_future(crawler(client, url_queue, archive))
        crawler_future.add_done_callback(task_completed)
        tasks.append(crawler_future)

    await wait_for(url_queue.join(), TIMEOUT)

    for task in tasks:
        task.cancel()
    client.close()

    webarchive = {
        'WebMainResource': archive['items'].pop(0),
        'WebSubresources': archive['items']
    }

    writePlist(webarchive, OUTPUT_FILENAME)


if __name__ == '__main__':
    client = ClientSession()
    loop = get_event_loop()
    loop.run_until_complete(scrape(client, TARGET_URL))
