from scrapy import log
from scrapy.contrib.spiders.sitemap import SitemapSpider
from scrapy.http import Request, HtmlResponse
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor

from ..scanner.scanner import Scanner

class ScannerSpider(SitemapSpider):
    name = 'scanner'

    def __init__(self, scan_id, *a, **kw):
        # Create scanner
        self.scanner = Scanner(scan_id)

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
        self.link_extractor = SgmlLinkExtractor(deny_extensions=(), tags=('a', 'area', 'frame', 'iframe', 'img'), attrs=('href', 'src'))

    def start_requests(self):
        """Start the spider with requests for all starting URLs AND sitemap URLs"""
        requests = [Request(url, callback=self.parse) for url in self.start_urls]
        requests.extend(list(SitemapSpider.start_requests(self)))
        return requests

    def parse(self, response):
        """Process a response and follow all links"""
        r = []
        r.extend(self._extract_requests(response))
        r.extend(self.scan(response))
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
        matches = self.scanner.scan(response)
        return matches