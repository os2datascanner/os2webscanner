#!/usr/bin/env python
import os
import sys

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"

from twisted.internet import reactor
from scrapy.crawler import Crawler
from scrapy import log, signals
from scrapy.utils.project import get_project_settings
from scanner.spiders.scanner_spider import ScannerSpider
from scrapy.exceptions import DontCloseSpider

from django.utils import timezone

from scanner.scanner.scanner import Scanner
from os2webscanner.models import Scan, ConversionQueueItem

from scanner.processors import *

import signal


def signal_handler(signal, frame):
    scanner_app.handle_killed()
    reactor.stop()


signal.signal(signal.SIGINT | signal.SIGTERM, signal_handler)


class ScannerApp:
    def __init__(self):
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
        self.run_spider()

    def handle_killed(self):
        self.scan_object = Scan.objects.get(pk=self.scan_id)
        self.scan_object.pid = None
        self.scan_object.status = Scan.FAILED
        self.scan_object.reason = "Killed"
        self.scan_object.save()

    def run_spider(self):
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

    def handle_closed(self, spider, reason):
        scan_object = Scan.objects.get(pk=self.scan_id)
        scan_object.status = Scan.DONE
        scan_object.pid = None
        scan_object.reason = ""
        scan_object.end_time = timezone.now()
        scan_object.save()
        # TODO: Check reason for if it was finished, cancelled, or shutdown
        reactor.stop()

    def handle_error(self, failure, response, spider):
        log.msg("Scan failed: %s" % failure.getErrorMessage(), level=log.ERROR)
        scan_object = Scan.objects.get(pk=self.scan_id)
        scan_object.status = Scan.FAILED
        scan_object.end_time = timezone.now()
        scan_object.reason = failure.getErrorMessage()
        scan_object.save()

    def handle_idle(self, spider):
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
