from urlparse import urlparse
from scrapy.http import Request, HtmlResponse
from scrapy.spider import Spider
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy import log

class FollowAllSpider(Spider):
    name = 'followall'

    def __init__(self, *a, **kw):
        super(FollowAllSpider, self).__init__(*a, **kw)
        url = kw.get('url')
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'http://%s/' % url
        self.url = url
        self.allowed_domains = [urlparse(url).hostname.lstrip('www.')]
        # TODO: Add more tags to extract links from?
        self.link_extractor = SgmlLinkExtractor(deny_extensions=(), tags=('a', 'area', 'frame', 'iframe', 'img'), attrs=('href', 'src'))

    def start_requests(self):
        # return []
        return [Request(self.url, callback=self.parse)]

    def parse(self, response):
        """Process a response and follow all links
        """
        r = []
        r.extend(self._extract_requests(response))
        r.extend(self.scan(response))
        return r

    def scan(self, response):
        """Callback for each response.
        Must be overridden
        :param response:
        :return:
        """
        raise NotImplementedError

    def _extract_requests(self, response):
        r = []
        if isinstance(response, HtmlResponse):
            links = self.link_extractor.extract_links(response)
            r.extend(Request(x.url, callback=self.parse) for x in links)
        return r
