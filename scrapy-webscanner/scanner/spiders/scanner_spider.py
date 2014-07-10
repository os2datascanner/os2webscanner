"""Contains a scanner spider."""

from scrapy import log
from scrapy.contrib.spiders.sitemap import SitemapSpider
from scrapy.http import Request, HtmlResponse
from scrapy.contrib.linkextractors.lxmlhtml import LxmlLinkExtractor

import re
import chardet
import mimetypes
import magic

from ..processors.processor import Processor

from os2webscanner.models import Url


class ScannerSpider(SitemapSpider):

    """A spider which uses a scanner to scan all data it comes across."""

    name = 'scanner'
    magic = magic.Magic(mime=True)

    def __init__(self, scanner, *a, **kw):
        """Initialize the ScannerSpider with a Scanner object.

        The configuration will be loaded from the Scanner.
        """
        # Create scanner
        self.scanner = scanner

        self.exclusion_rules = self.scanner.get_exclusion_rules()
        self.allowed_domains = self.scanner.get_domains()
        self.sitemap_urls = self.scanner.get_sitemap_urls()

        # Follow alternate links in sitemaps (links to the same content in
        # different languages)
        self.sitemap_alternate_links = True

        SitemapSpider.__init__(self, *a, **kw)

        self.start_urls = []
        # TODO: Starting URLs and domains should be specified separately?
        for url in self.allowed_domains:
            if (not url.startswith('http://')
                and not url.startswith('https://')):
                url = 'http://%s/' % url
            self.start_urls.append(url)

        # TODO: Add more tags to extract links from?
        self.link_extractor = LxmlLinkExtractor(
            deny_extensions=(),
            tags=('a', 'area', 'frame', 'iframe', 'script'),
            attrs=('href', 'src')
        )

    def start_requests(self):
        """Return requests for all starting URLs AND sitemap URLs."""
        requests = [Request(url, callback=self.parse)
                    for url in self.start_urls]
        requests.extend(list(SitemapSpider.start_requests(self)))
        return requests

    def parse(self, response):
        """Process a response and follow all links."""
        r = []
        r.extend(self._extract_requests(response))
        self.scan(response)
        return r

    def _extract_requests(self, response):
        """Extract requests from the response."""
        r = []
        if isinstance(response, HtmlResponse):
            links = self.link_extractor.extract_links(response)
            log.msg("Extracted links: %s" % links, level=log.DEBUG)
            r.extend(Request(x.url, callback=self.parse) for x in links)
        return r

    def scan(self, response):
        """Scan a response, returning any matches."""
        content_type = response.headers.get('content-type')
        if content_type:
            mime_type = parse_content_type(content_type)
            log.msg("Content-Type: " + content_type, level=log.DEBUG)
        else:
            log.msg("Guessing mime-type based on file extension",
                    level=log.DEBUG)
            mime_type, encoding = mimetypes.guess_type(response.url)
            # Scrapy already guesses the encoding.. we don't need it

        if hasattr(response, "encoding"):
            try:
                data = response.body.decode(response.encoding)
            except UnicodeDecodeError, e:
                try:
                    # Encoding specified in Content-Type header was wrong, try
                    # to detect the encoding and decode again
                    encoding = chardet.detect(response.body).get('encoding')
                    if encoding is not None:
                        data = response.body.decode(encoding)
                        log.msg(("Error decoding response as %s. " +
                                 "Detected the encoding as %s.") % (
                                    response.encoding, encoding))
                    else:
                        mime_type = self.magic.from_buffer(response.body)
                        data = response.body
                        log.msg(("Error decoding response as %s. " +
                                 "Detected the mime " +
                                 "type as %s.") % (response.encoding,
                                                   mime_type))
                except UnicodeDecodeError, e:
                    # Could not decode with the detected encoding, so assume
                    # the file is binary and try to guess the mimetype from
                    # the file
                    mime_type = self.magic.from_buffer(response.body)
                    data = response.body
                    log.msg(
                        ("Error decoding response as %s. Detected the "
                         "mime type as %s.") % (response.encoding,
                                                mime_type)
                    )

        else:
            data = response.body

        # Save the URL item to the database
        if (Processor.mimetype_to_processor_type(mime_type) == 'ocr' and not
            self.scanner.scan_object.do_ocr):
            # Ignore this URL
            return
        url_object = Url(url=response.request.url, mime_type=mime_type,
                         scan=self.scanner.scan_object)
        url_object.save()
        result = self.scanner.scan(data, url_object)


def parse_content_type(content_type):
    """Return the mime-type from the given "Content-Type" header value."""
    m = re.search('([^/]+/[^;\s]+)', content_type)
    return m.group(1)
