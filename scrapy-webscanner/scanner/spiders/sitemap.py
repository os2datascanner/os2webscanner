"""Sitemap spider which gathers URLs contained in sitemap files."""

from scrapy.contrib.spiders import SitemapSpider
from scrapy.contrib.spiders.sitemap import iterloc
from scrapy.utils.sitemap import Sitemap, sitemap_urls_from_robots

from scrapy.http import Request
from scrapy import log

from .base_spider import BaseScannerSpider

import dateutil.parser
import datetime
import pytz


class SitemapURLGathererSpider(BaseScannerSpider, SitemapSpider):

    """A sitemap spider that stores URLs found in the sitemaps provided."""

    name = 'sitemap_url_gatherer'

    def __init__(self, scanner, sitemap_urls, uploaded_sitemap_urls,
                 sitemap_alternate_links,
                 *a,
                 **kw):
        """Initialize the sitemap spider."""
        super(SitemapURLGathererSpider, self).__init__(scanner=scanner, *a,
                                                       **kw)
        self.sitemap_urls = sitemap_urls
        self.uploaded_sitemap_urls = uploaded_sitemap_urls
        self.sitemap_alternate_links = sitemap_alternate_links
        self.urls = []

    def start_requests(self):
        requests = []
        for x in self.sitemap_urls:
            requests.append(Request(x, callback=self._parse_sitemap))

        # Add requests for uploaded sitemap files
        for x in self.uploaded_sitemap_urls:
            # Specify dont_filter because this is an uploaded sitemap file
            # with a file:// URL and we don't want it filtered as an offsite
            # request.
            requests.append(Request(x, callback=self._parse_sitemap,
                                    dont_filter=True))
        return requests

    def _parse_sitemap(self, response):
        log.msg("Parsing sitemap %s" % response)
        if response.url.endswith('/robots.txt'):
            for url in sitemap_urls_from_robots(response.body):
                yield Request(url, callback=self._parse_sitemap)
        else:
            body = self._get_sitemap_body(response)
            if body is None:
                log.msg(format="Ignoring invalid sitemap: %(response)s",
                        level=log.WARNING, spider=self, response=response)
                return
            s = Sitemap(body)
            if s.type == 'sitemapindex':
                for loc in iterloc(s, self.sitemap_alternate_links):
                    if any(x.search(loc) for x in self._follow):
                        yield Request(loc, callback=self._parse_sitemap)
            elif s.type == 'urlset':
                for url in iter(s):
                    loc = url['loc']
                    # Add the lastmod date to the Request meta
                    lastmod = url.get('lastmod', None)
                    if lastmod is not None:
                        lastmod = parse_w3c_datetime(lastmod)
                    for r, c in self._cbs:
                        if r.search(loc):
                            self.urls.append({"url": loc, "lastmod": lastmod})
                            break

    def get_urls(self):
        """Return a list of URLs found in the sitemap.

        Each URL is a dict containing keys 'url' and 'lastmod'.
        """
        return self.urls


def parse_w3c_datetime(date_str):
    """Parse a W3C date-time string into a datetime object."""
    # Timezone is assumed to be UTC if not specified
    return dateutil.parser.parse(date_str,
                                 default=datetime.datetime.now().
                                 replace(hour=0, minute=0, second=0,
                                         microsecond=0, tzinfo=pytz.UTC))
