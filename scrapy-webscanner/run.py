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
import urllib2
from urlparse import urlparse

import os
import sys

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"

os.environ["SCRAPY_SETTINGS_MODULE"] = "scanner.settings"

from twisted.internet import reactor
from scrapy.crawler import Crawler
from scrapy import log, signals
from scrapy.utils.project import get_project_settings
from scanner.spiders.scanner_spider import ScannerSpider
from scrapy.exceptions import DontCloseSpider

from django.utils import timezone

from scanner.scanner.scanner import Scanner
from os2webscanner.models import Scan, ConversionQueueItem, Url, ReferrerUrl

import linkchecker

from scanner.processors import *

import signal

# Activate timezone from settings
timezone.activate(timezone.get_default_timezone())


def signal_handler(signal, frame):
    """Handle being killed."""
    scanner_app.handle_killed()
    reactor.stop()


signal.signal(signal.SIGINT | signal.SIGTERM, signal_handler)


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
        """Run the scanner."""
        self.run_spider()

    def handle_killed(self):
        """Handle being killed by updating the scan status."""
        self.scan_object = Scan.objects.get(pk=self.scan_id)
        self.scan_object.pid = None
        self.scan_object.status = Scan.FAILED
        self.scan_object.reason = "Killed"
        # TODO: Remove all non-processed conversion queue items.
        self.scan_object.save()

    def run_spider(self):
        """Run the scanner spider and block until it finishes."""
        spider = ScannerSpider(self.scanner)
        settings = get_project_settings()
        crawler = Crawler(settings)
        crawler.signals.connect(self.handle_closed,
                                signal=signals.spider_closed)
        crawler.signals.connect(self.handle_error, signal=signals.spider_error)
        crawler.signals.connect(self.handle_idle, signal=signals.spider_idle)
        crawler.configure()
        crawler.crawl(spider)
        crawler.start()
        log.start()
        # the script will block here until the spider_closed signal was sent
        reactor.run()

        if spider.scanner.do_link_check:
            if spider.scanner.do_external_link_check:
                self.external_link_check(spider.external_urls)
            self.associate_referrers(spider.referrers)

        # Update scan status
        scan_object = Scan.objects.get(pk=self.scan_id)
        scan_object.status = Scan.DONE
        scan_object.pid = None
        scan_object.reason = ""
        scan_object.save()

    def external_link_check(self, external_urls):
        """Perform external link checking."""
        log.msg("Performing external link check...")
        for url in external_urls:
            url_parse = urlparse(url)
            if url_parse.scheme not in ("http", "https"):
                # We don't want to allow external URL checking of other
                # schemes (file:// for example)
                continue
            result = linkchecker.check_url(url)
            if result is not None:
                broken_url = Url(url=url, scan=self.scan_object,
                                 status_code=result["status_code"],
                                 status_message=result["status_message"])
                broken_url.save()

    def associate_referrers(self, referrers):
        """Associate referrers with broken URLs."""

        # Dict to cache referrer URL objects
        referrer_url_objects = {}

        # Iterate through all broken URLs
        url_objects = Url.objects.filter(scan=self.scan_object).exclude(
            status_code__isnull=True
        )
        for url_object in url_objects:
            # Associate the referrers with URL objects
            if not hasattr(referrers, url_object.url):
                # Skip URLs with no referrers (f.x. starting URLs)
                continue
            for referrer in referrers[url_object.url]:
                # Create or get existing referrer URL object
                if not referrer in referrer_url_objects:
                    referrer_url_objects[referrer] = ReferrerUrl(
                        url=referrer, scan=self.scan_object)
                    referrer_url_objects[referrer].save()
                referrer_url_object = referrer_url_objects[referrer]
                url_object.referrers.add(referrer_url_object)
            url_object.save()

    def handle_closed(self, spider, reason):
        """Handle the spider being finished"""
        # TODO: Check reason for if it was finished, cancelled, or shutdown
        reactor.stop()

    def handle_error(self, failure, response, spider):
        """Handle spider errors, updating scan status."""
        log.msg("Scan failed: %s" % failure.getErrorMessage(), level=log.ERROR)
        scan_object = Scan.objects.get(pk=self.scan_id)
        scan_object.reason = failure.getErrorMessage()
        scan_object.save()

    def handle_idle(self, spider):
        """Handle when the spider is idle.

        Keep it open if there are still queue items to be processed.
        """
        log.msg("Spider Idle...")
        # Keep spider alive if there are still queue items to be processed
        remaining_queue_items = ConversionQueueItem.objects.filter(
            status__in=[ConversionQueueItem.NEW,
                        ConversionQueueItem.PROCESSING],
            url__scan=self.scan_object
        ).count()

        if remaining_queue_items > 0:
            log.msg(
                "Keeping spider alive: %d remaining queue items to process" %
                remaining_queue_items
            )
            raise DontCloseSpider
        else:
            log.msg("No more active processors, closing spider...")


scanner_app = ScannerApp()
scanner_app.run()
