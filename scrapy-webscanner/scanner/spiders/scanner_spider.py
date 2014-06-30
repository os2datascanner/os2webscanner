from scrapy import log
from scrapy.contrib.spiders.sitemap import SitemapSpider
from scrapy.http import Request, HtmlResponse
from scrapy.contrib.linkextractors.lxmlhtml import LxmlLinkExtractor

import re
import chardet

from os2webscanner.models import Url

class ScannerSpider(SitemapSpider):
    name = 'scanner'

    def __init__(self, scanner, *a, **kw):
        # Create scanner
        self.scanner = scanner

        self.allowed_domains = self.scanner.get_domains()
        self.sitemap_urls = self.scanner.get_sitemap_urls()

        # Follow alternate links in sitemaps (links to the same content in
        # different languages)
        self.sitemap_alternate_links = True

        SitemapSpider.__init__(self, *a, **kw)

        self.start_urls = []
        # TODO: Starting URLs and domains should be specified separately?
        for url in self.allowed_domains:
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'http://%s/' % url
            self.start_urls.append(url)

        # TODO: Add more tags to extract links from?
        # self.link_extractor = SgmlLinkExtractor(deny_extensions=(), tags=('a', 'area', 'frame', 'iframe', 'img'), attrs=('href', 'src'))
        self.link_extractor = LxmlLinkExtractor(deny_extensions=(), tags=('a', 'area', 'frame', 'iframe', 'img'), attrs=('href', 'src'))

    def start_requests(self):
        """Start the spider with requests for all starting URLs AND sitemap URLs"""
        requests = [Request(url, callback=self.parse) for url in self.start_urls]
        requests.extend(list(SitemapSpider.start_requests(self)))
        return requests

    def parse(self, response):
        """Process a response and follow all links"""
        first_try = True
        while True:
            r = []
            try:
                r.extend(self._extract_requests(response))
                self.scan(response)
                break
            except UnicodeDecodeError, e:
                if not first_try:
                    break
                first_try = True
                new_response = response.replace(encoding = chardet.detect(response.body).get('encoding'))
                log.msg(repr(e))
                log.msg("Error decoding response as %s. Detected encoding as %s and trying again." % (response.encoding, new_response.encoding))
                continue
        return r

    def _extract_requests(self, response):
        """Extract requests from the response"""
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
            log.msg("Guessing mime-type based on file extension", level=log.DEBUG)
            mime_type, encoding = mimetypes.guess_type(response.url)
            # Scrapy already guesses the encoding.. we don't need it

        if hasattr(response, "encoding"):
            data = response.body.decode(response.encoding)
        else:
            data = response.body

        # Save the URL item to the database
        url_object = Url(url=response.url, mime_type=mime_type, scan=self.scanner.scan_object)
        url_object.save()
        self.scanner.scan(data, matches_callback=lambda matches: self.process_matches(matches, url_object), mime_type=mime_type, url=response.url)

    def process_matches(self, matches, url_object):
        for match in matches:
            match.url = url_object
            match.scan = self.scanner.scan_object
            log.msg("Match: " + str(match))
            match.save()

def parse_content_type(content_type):
    """Parses and returns the mime-type from a Content-Type header value"""
    m = re.search('([^/]+/[^;\s]+)', content_type)
    return m.group(1)