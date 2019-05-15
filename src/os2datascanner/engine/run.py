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

import logging

from dateutil.parser import parse as parse_datetime

from twisted.internet import reactor, defer
from scrapy import signals
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
from scrapy.exceptions import DontCloseSpider

import os
from sys import stderr
os.umask(0o007)
os.environ["SCRAPY_SETTINGS_MODULE"] = "os2datascanner.engine.scanners.settings"

# django_setup needs to be loaded before any imports from django app os2webscanner
from .utils import run_django_setup

run_django_setup()

# Activate timezone from settings
from django.utils import timezone
timezone.activate(timezone.get_default_timezone())


class StartScan(object):
    """A scanner application which can be run."""

    def __init__(self, configuration):
        """
        Initialize the scanner application.
        Takes the JSON descriptor of this scan as its argument.
        """
        super().__init__()
        self.configuration = configuration

        scan_id = configuration['id']
        logfile = configuration['logfile']
        last_started = configuration['last_started']

        self.scan_id = scan_id
        self.logfile = logfile
        self.last_started = \
            parse_datetime(last_started) if last_started else None
        self.sitemap_crawler = None
        self.scanner_crawler = None

        self.settings = get_project_settings()
        self.crawler_process = None

    def run(self):
        """Updates the scan status and sets the pid.
        Run the scanner, blocking until finished."""

        # Each scanner process should set up logging separately, writing to
        # both the log file and to the scanner manager's standard error stream
        logging.basicConfig(
                level=logging.DEBUG,
                format="""\
%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s""",
                handlers=[
                    logging.FileHandler(self.logfile),
                    logging.StreamHandler(stderr)
                ])

        # Scrapy expects to be able to log things, so this call should always
        # happen after we've initialised the root logging handler
        self.crawler_process = \
            CrawlerProcess(self.settings, install_root_handler=False)

        # A new instance of django setup needs to be loaded for the scan process,
        # so the django db connection is not shared between processors.
        from .utils import run_django_setup
        run_django_setup()

    def handle_killed(self):
        """Handle being killed by updating the scan status."""
        self.scanner.failed()
        self.scan.logging_occurrence("SCANNER FAILED: Killed")
        logging.error("Killed")

    def make_scanner_crawler(self, spider_type):
        """Setup the scanner spider and crawler."""
        self.scanner_crawler = \
            self.crawler_process.create_crawler(spider_type)
        csigs = self.scanner_crawler.signals
        csigs.connect(self.handle_closed, signal=signals.spider_closed)
        csigs.connect(self.handle_error, signal=signals.spider_error)
        csigs.connect(self.handle_idle, signal=signals.spider_idle)
        return self.scanner_crawler

    def handle_closed(self, spider, reason):
        """Handle the spider being finished."""
        # TODO: Check reason for if it was finished, cancelled, or shutdown
        logging.debug('Spider is closing. Reason {0}'.format(reason))
        self.store_stats()
        reactor.stop()

    def store_stats(self):
        """Stores scrapy scanning stats when scan is completed."""
        from ..sites.admin.adminapp.models.statistic_model import Statistic
        from django.core.exceptions import MultipleObjectsReturned
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

    def handle_idle(self, spider):
        """Handle when the spider is idle.

        Keep it open if there are still queue items to be processed.
        """
        from ..sites.admin.adminapp.models.conversionqueueitem_model import ConversionQueueItem
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

