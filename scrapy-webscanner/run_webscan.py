import logging
import linkchecker
import multiprocessing

from urllib.parse import urlparse

from twisted.internet import reactor, defer

from run import StartScan

from scanners.spiders.sitemap import SitemapURLGathererSpider
from scanners.scanner_types.webscanner import WebScanner
from scanners.spiders.webspider import WebSpider


class StartWebScan(StartScan, multiprocessing.Process):
    """A scanner application which can be run."""

    def __init__(self, scan_id, logfile=None, last_started=None):
        """
        Initialize the scanner application.
        Takes scan id as input, which is directly related to the scan job id in the database.
        """

        super().__init__(scan_id, logfile, last_started)
        multiprocessing.Process.__init__(self)

    def run(self):
        """Updates the scan status and sets the pid.
        Run the scanner, blocking until finished."""
        super().run()
        self.scanner = WebScanner(self.scan_id)
        if self.scanner.scan_object.status is not "STARTED":
            self.scanner.scan_object.set_scan_status_start()

        self.start_webscan_crawlers()

        self.scanner.scan_object.set_scan_status_done()

    def start_webscan_crawlers(self):
        logging.info("Beginning crawler process.")
        self.run_crawlers()
        self.crawler_process.start()
        logging.info("Crawler process finished.")

        if (self.scanner.scan_object.do_link_check
            and self.scanner.scan_object.do_external_link_check):
            # Do external link check
            self.external_link_check(self.scanner_crawler.spider.external_urls)


    @defer.inlineCallbacks
    def run_crawlers(self):
        # Don't sitemap scan when running over RPC or if no sitemap is set on
        if not self.scanner.scan_object.scanner.process_urls:
            if len(self.scanner.get_sitemap_urls()) is not 0 \
                    or len(self.scanner.get_uploaded_sitemap_urls()) is not 0:
                yield self.crawler_process.crawl(self.make_sitemap_crawler(),
                                                 scanner=self.scanner,
                                                 runner=self,
                                                 sitemap_urls=self.scanner.get_sitemap_urls(),
                                                 uploaded_sitemap_urls=
                                                 self.scanner.get_uploaded_sitemap_urls(),
                                                 sitemap_alternate_links=True)

        self.make_scanner_crawler(WebSpider)
        yield self.crawler_process.crawl(self.scanner_crawler,
                                         scanner=self.scanner,
                                         runner=self)
    def make_sitemap_crawler(self):
        """Setup the sitemap spider and crawler."""
        self.sitemap_crawler = \
            self.crawler_process.create_crawler(SitemapURLGathererSpider)
        return self.sitemap_crawler

    def get_start_urls_from_sitemap(self):
        """Return the URLs found by the sitemap spider."""
        if self.sitemap_crawler is not None:
            logging.debug('Sitemap spider found')
            return self.sitemap_crawler.spider.get_urls()
        else:
            return []

    def external_link_check(self, external_urls):
        """Perform external link checking."""
        from os2webscanner.models.url_model import Url
        logging.info("Link checking %d external URLs..." % len(external_urls))

        for url in external_urls:
            url_parse = urlparse(url)
            if url_parse.scheme not in ("http", "https"):
                # We don't want to allow external URL checking of other
                # schemes (file:// for example)
                continue

            logging.info("Checking external URL %s" % url)

            result = linkchecker.check_url(url)
            if result is not None:
                broken_url = Url(url=url, scan=self.scanner.scan_object.webscan,
                                 status_code=result["status_code"],
                                 status_message=result["status_message"])
                broken_url.save()
                self.scanner_crawler.spider.associate_url_referrers(broken_url)
