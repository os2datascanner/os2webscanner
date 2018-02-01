#!/usr/bin/env python
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
"""Run a scan by Scan ID."""
import collections
from urllib.parse import urlparse

import os
import sys
import django

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"
django.setup()

os.umask(0o007)

os.environ["SCRAPY_SETTINGS_MODULE"] = "scanner.settings"

from twisted.internet import reactor
from scrapy.crawler import CrawlerProcess
from scrapy import signals
from scrapy.utils.project import get_project_settings
from scanner.spiders.scanner_spider import ScannerSpider
from scanner.spiders.sitemap import SitemapURLGathererSpider

from scrapy.exceptions import DontCloseSpider

from django.utils import timezone

from scanner.scanner.scanner import Scanner
from os2webscanner.models import Scan, ConversionQueueItem, Url

import linkchecker
import logging

from scanner.processors import *  # noqa

import signal

# Activate timezone from settings
timezone.activate(timezone.get_default_timezone())


def signal_handler(signal, frame):
    """Handle being killed."""
    scanner_app.handle_killed()
    reactor.stop()


signal.signal(signal.SIGINT | signal.SIGTERM, signal_handler)


class OrderedCrawlerProcess(CrawlerProcess):

    """Override CrawlerProcess to use an ordered dict."""

    crawlers = None

    def __init__(self, *a, **kw):
        """Initialize the CrawlerProcess with an OrderedDict of crawlers."""
        super().__init__(*a, **kw)
        self.crawlers = collections.OrderedDict()

    def _start_crawler(self):
        """Override this method to pop the first crawler instead of last."""
        if not self.crawlers or self.stopping:
            return

        name, crawler = self.crawlers.popitem(last=False)
        self._active_crawler = crawler
        sflo = logging.start_from_crawler(crawler)
        crawler.configure()
        crawler.install()
        crawler.signals.connect(crawler.uninstall, signals.engine_stopped)
        if sflo:
            crawler.signals.connect(sflo.stop, signals.engine_stopped)
        crawler.signals.connect(self._check_done, signals.engine_stopped)
        crawler.start()
        return name, crawler


class ScannerApp:
    """A scanner application which can be run."""

    def __init__(self):
        """Initialize the scanner application.

        Updates the scan status and sets the pid.
        """
        self.scan_id = sys.argv[1]

        # Get scan object from DB
        self.scan_object = Scan.objects.get(pk=self.scan_id)

        # Update start_time to now and status to STARTED
        self.scan_object.start_time = timezone.now()
        self.scan_object.status = Scan.STARTED
        self.scan_object.reason = ""
        self.scan_object.pid = os.getpid()
        self.scan_object.save()

        self.scanner = Scanner(self.scan_id)

    def run(self):
        """Run the scanner, blocking until finished."""
        settings = get_project_settings()

        # job_dir = os.path.join(self.scan_object.scan_dir, 'job')
        # settings.set('JOBDIR', job_dir)

        self.crawler_process = OrderedCrawlerProcess(settings)

        # Don't sitemap scan when running over RPC
        if not self.scan_object.scanner.process_urls:
            self.sitemap_spider = self.setup_sitemap_spider()
        self.scanner_spider = self.setup_scanner_spider()

        # Run the crawlers and block
        self.crawler_process.start()

        if (self.scanner.scan_object.do_link_check
                and self.scanner.scan_object.do_external_link_check):
            # Do external link check
            self.external_link_check(self.scanner_spider.external_urls)

        # Update scan status
        scan_object = Scan.objects.get(pk=self.scan_id)
        scan_object.status = Scan.DONE
        scan_object.pid = None
        scan_object.reason = ""
        scan_object.save()

    def handle_killed(self):
        """Handle being killed by updating the scan status."""
        self.scan_object = Scan.objects.get(pk=self.scan_id)
        self.scan_object.pid = None
        self.scan_object.status = Scan.FAILED
        self.scan.logging_occurrence("SCANNER FAILED: Killed")
        logging.error("Killed")
        self.scan_object.reason = "Killed"
        # TODO: Remove all non-processed conversion queue items.
        self.scan_object.save()

    def setup_sitemap_spider(self):
        """Setup the sitemap spider."""
        crawler = self.crawler_process.create_crawler(SitemapURLGathererSpider)
        crawler.crawl(
            scanner=self.scanner,
            sitemap_urls=self.scanner.get_sitemap_urls(),
            uploaded_sitemap_urls=self.scanner.get_uploaded_sitemap_urls(),
            sitemap_alternate_links=True
            )
        return crawler.spider

    def setup_scanner_spider(self):
        """Setup the scanner spider."""
        crawler = self.crawler_process.create_crawler(ScannerSpider)
        spider = ScannerSpider(self.scanner, self)
        crawler.signals.connect(self.handle_closed,
                                signal=signals.spider_closed)
        crawler.signals.connect(self.handle_error, signal=signals.spider_error)
        crawler.signals.connect(self.handle_idle, signal=signals.spider_idle)
        crawler.crawl(scanner=self.scanner, runner=self)
        return crawler.spider

    def get_start_urls_from_sitemap(self):
        """Return the URLs found by the sitemap spider."""
        if hasattr(self, "sitemap_spider"):
            return self.sitemap_spider.get_urls()
        else:
            return []

    def external_link_check(self, external_urls):
        """Perform external link checking."""
        print("Link checking %d external URLs..." % len(external_urls))
        for url in external_urls:
            url_parse = urlparse(url)
            if url_parse.scheme not in ("http", "https"):
                # We don't want to allow external URL checking of other
                # schemes (file:// for example)
                continue
            print("Checking external URL %s" % url)
            result = linkchecker.check_url(url)
            if result is not None:
                broken_url = Url(url=url, scan=self.scan_object,
                                 status_code=result["status_code"],
                                 status_message=result["status_message"])
                broken_url.save()
                self.scanner_spider.associate_url_referrers(broken_url)

    def handle_closed(self, spider, reason):
        """Handle the spider being finished."""
        # TODO: Check reason for if it was finished, cancelled, or shutdown
        reactor.stop()

    def handle_error(self, failure, response, spider):
        """Handle spider errors, updating scan status."""
        logging.msg("Scan failed: %s" % failure.getErrorMessage(),
                    level=logging.ERROR)
        scan_object = Scan.objects.get(pk=self.scan_id)
        scan_object.reason = failure.getErrorMessage()
        scan_object.save()

    def handle_idle(self, spider):
        """Handle when the spider is idle.

        Keep it open if there are still queue items to be processed.
        """
        logging.msg("Spider Idle...")
        # Keep spider alive if there are still queue items to be processed
        remaining_queue_items = ConversionQueueItem.objects.filter(
            status__in=[ConversionQueueItem.NEW,
                        ConversionQueueItem.PROCESSING],
            url__scan=self.scan_object
        ).count()

        if remaining_queue_items > 0:
            logging.msg(
                "Keeping spider alive: %d remaining queue items to process" %
                remaining_queue_items
            )
            raise DontCloseSpider
        else:
            logging.msg("No more active processors, closing spider...")


scanner_app = ScannerApp()
scanner_app.run()
