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
from urllib.parse import urlparse
import multiprocessing

import os
import sys
import django
# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"

os.umask(0o007)
os.environ["SCRAPY_SETTINGS_MODULE"] = "scanner.settings"

django.setup()

from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerProcess
from scrapy import signals
from scrapy.utils.project import get_project_settings
from scanner.spiders.scanner_spider import ScannerSpider
from scanner.spiders.sitemap import SitemapURLGathererSpider

from scrapy.exceptions import DontCloseSpider

from django.utils import timezone
from django.core.exceptions import MultipleObjectsReturned

from scanner.scanner.scanner import Scanner
from os2webscanner.models.scan_model import Scan
from os2webscanner.models.statistic_model import Statistic
from os2webscanner.models.conversionqueueitem_model import ConversionQueueItem
from os2webscanner.models.url_model import Url

import linkchecker

# import signal

import logging

# Activate timezone from settings
timezone.activate(timezone.get_default_timezone())


# def signal_handler(signal, frame):
#     """Handle being killed."""
#     scanner_app.handle_killed()
#     reactor.stop()


# signal.signal(signal.SIGINT | signal.SIGTERM, signal_handler)


class ScannerApp(multiprocessing.Process):
    """A scanner application which can be run."""

    def __init__(self, scan_id, scanner_type, logfile=None):
        """
        Initialize the scanner application.
        Takes scan id as input, which is directly related to the scan job id in the database.
        """
        multiprocessing.Process.__init__(self)
        self.scan_id = scan_id
        # For now scanner_type is not used...
        self.scanner_type = scanner_type
        self.logfile = logfile
        self.sitemap_crawler = None
        self.scanner_crawler = None

    def run(self):
        """Updates the scan status and sets the pid.
        Run the scanner, blocking until finished."""
        django.setup()
        logging.basicConfig(filename=self.logfile, level=logging.DEBUG)

        self.scanner = Scanner(self.scan_id)

        if self.scanner.scan_object.status is not Scan.STARTED:
            self.scanner.scan_object.set_scan_status_start()

        settings = get_project_settings()

        self.crawler_process = CrawlerProcess(settings)

        if hasattr(self.scanner.scan_object, 'webscan'):
            self.start_webscan_crawlers()
        else:
            self.start_filescan_crawlers()

        # Update scan status
        self.scanner.scan_object.set_scan_status_done()

    def start_filescan_crawlers(self):
        """Start a file scan."""

        logging.info("Beginning crawler process.")
        self.run_crawlers()
        self.crawler_process.start()
        logging.info("Crawler process finished.")

    def start_webscan_crawlers(self):
        logging.info("Beginning crawler process.")
        self.run_crawlers()
        self.crawler_process.start()
        logging.info("Crawler process finished.")

        if (self.scanner.scan_object.webscan.do_link_check
            and self.scanner.scan_object.webscan.do_external_link_check):
            # Do external link check
            self.external_link_check(self.scanner_crawler.spider.external_urls)

    @defer.inlineCallbacks
    def run_crawlers(self):
        # Don't sitemap scan when running over RPC or if no sitemap is set on
        # scan (or if the scanner isn't a web scanner!)
        if hasattr(self.scanner.scan_object, 'webscan') \
                and not self.scanner.scan_object.scanner.process_urls:
            if len(self.scanner.get_sitemap_urls()) is not 0\
                    or len(self.scanner.get_uploaded_sitemap_urls()) is not 0:
                yield self.crawler_process.crawl(self.make_sitemap_crawler(),
                        scanner=self.scanner,
                        runner=self,
                        sitemap_urls=self.scanner.get_sitemap_urls(),
                        uploaded_sitemap_urls=
                            self.scanner.get_uploaded_sitemap_urls(),
                        sitemap_alternate_links=True)
        yield self.crawler_process.crawl(self.make_scanner_crawler(),
                scanner=self.scanner, runner=self)

    def handle_killed(self):
        """Handle being killed by updating the scan status."""
        self.scanner.scan_object = Scan.objects.get(pk=self.scan_id)
        self.scanner.scan_object.set_scan_status_failed()
        self.scan.logging_occurrence("SCANNER FAILED: Killed")
        logging.error("Killed")

    def make_sitemap_crawler(self):
        """Setup the sitemap spider and crawler."""
        self.sitemap_crawler = \
            self.crawler_process.create_crawler(SitemapURLGathererSpider)
        return self.sitemap_crawler

    def make_scanner_crawler(self):
        """Setup the scanner spider and crawler."""
        self.scanner_crawler = \
            self.crawler_process.create_crawler(ScannerSpider)
        csigs = self.scanner_crawler.signals
        csigs.connect(self.handle_closed, signal=signals.spider_closed)
        csigs.connect(self.handle_error, signal=signals.spider_error)
        csigs.connect(self.handle_idle, signal=signals.spider_idle)
        return self.scanner_crawler

    def get_start_urls_from_sitemap(self):
        """Return the URLs found by the sitemap spider."""
        if self.sitemap_crawler is not None:
            logging.debug('Sitemap spider found')
            return self.sitemap_crawler.spider.get_urls()
        else:
            return []

    def external_link_check(self, external_urls):
        """Perform external link checking."""
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

    def handle_closed(self, spider, reason):
        """Handle the spider being finished."""
        # TODO: Check reason for if it was finished, cancelled, or shutdown
        logging.debug('Spider is closing. Reason {0}'.format(reason))
        self.store_stats()
        self.filescan_cleanup()
        reactor.stop()

    def store_stats(self):
        """Stores scrapy scanning stats when scan is completed."""
        logging.info('Stats: {0}'.format(self.scanner_crawler.stats.get_stats()))

        try:
            statistics, created = Statistic.objects.get_or_create(scan=self.scanner.scan_object)
        except MultipleObjectsReturned:
            logging.error('Multiple statistics objects found for scan job {}'.format(
                self.scan_id)
            )

        if self.scanner_crawler.stats.get_value(
                'last_modified_check/pages_skipped'):
            statistics.files_skipped_count += self.scanner_crawler.stats.get_value(
                'last_modified_check/pages_skipped'
            )
        if self.scanner_crawler.stats.get_value(
                'downloader/request_count'):
            statistics.files_scraped_count += self.scanner_crawler.stats.get_value(
                'downloader/request_count'
            )
        if self.scanner_crawler.stats.get_value(
                'downloader/exception_type_count/builtins.IsADirectoryError'):
            statistics.files_is_dir_count += self.scanner_crawler.stats.get_value(
                'downloader/exception_type_count/builtins.IsADirectoryError'
            )

        statistics.save()
        logging.debug('Statistic saved.')

    def handle_error(self, failure, response, spider):
        """Printing spider errors.

        When an exception occurs in a spider callback we do not need to stop the scan.
        The scan is only stopped when the spider signals it has stopped.

        So we only print the error to the log."""
        logging.error("An error occured: %s" % failure.getErrorMessage())

    def filescan_cleanup(self):
        if hasattr(self.scanner.scan_object, 'filescan'):
            for domain in self.scanner.valid_domains:
                domain.filedomain.smb_umount()

    def handle_idle(self, spider):
        """Handle when the spider is idle.

        Keep it open if there are still queue items to be processed.
        """
        logging.debug("Spider Idle...")
        # Keep spider alive if there are still queue items to be processed
        remaining_queue_items = ConversionQueueItem.objects.filter(
            status__in=[ConversionQueueItem.NEW,
                        ConversionQueueItem.PROCESSING],
            url__scan=self.scanner.scan_object
        ).count()

        if remaining_queue_items > 0:
            logging.info(
                "Keeping spider alive: %d remaining queue items to process" %
                remaining_queue_items
            )
            raise DontCloseSpider
        else:
            logging.info("No more active processors, closing spider...")

