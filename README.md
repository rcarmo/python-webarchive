# python-webarchive

This is a quick hack demonstrating how to create WebKit/Safari `.webarchive` files, inspired by [pocket-archive-stream][pas].

## Usage

```bash
TARGET_URL=http://foo.com python3 main.py
```

## Why `.webarchive`?

`.webarchive` is the native web page archive format on the Mac, and is essentially a serialized snapshot of Safari/WebKit state. On a Mac, these files are Spotlight-indexable and can be opened by just about anything that takes a "webpage" as input.

Despite the rising prominence of [WARC][warc] as the standard web archiving format (which to this day requires plug-ins to be viewable on a browser) I quite like `.webarchive`, and built this in order to both demonstrate how to use it and have a minimally viable archive creator I can deploy as a service.

## Anatomy of a `.webarchive` file

The file format is a nested binary `.plist`, with roughly the following structure:

```json
{
    "WebMainResource": {
        "WebResourceURL": String(),
        "WebResourceMIMEType": String(),
        "WebResourceResponse": NSKeyedArchiver(NSObject)),
        "WebResourceData": Bytes(),
        "WebResourceTextEncodingName": String(optional=True)
    },
    "WebSubresources": [
        {item, item, item...}
    ]

}
```

So creating a `.webarchive` turns out to be fairly straightforward if you simply build a `dict` with the right structure and then serialize it using [`biplist`][biplist] (which works on any platform).

The only hitch would be `WebResourceResponse` (which uses a [rather more complex way][nska] to encode the HTTP result headers), but fortunately that appears not to be necessary at all.

## Next Steps

* [ ] Tie this into [pocket-archive-stream][pas]
* [ ] Convert to/from [WARC][warc]
* [ ] Look into integrating with [warcprox][warcprox]

[biplist]: https://bitbucket.org/wooster/biplist
[pas]: https://github.com/pirate/pocket-archive-stream
[warc]: https://en.wikipedia.org/wiki/Web_ARChive
[warcprox]: https://github.com/internetarchive/warcprox
[nska]: https://www.mac4n6.com/blog/2016/1/1/manual-analysis-of-nskeyedarchiver-formatted-plist-files-a-review-of-the-new-os-x-1011-recent-items
