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

from django.utils import timezone

from os2webscanner.models import Scan

scan_id = sys.argv[1]

def handle_closed(spider, reason):
    scan_object = Scan.objects.get(pk=scan_id)
    scan_object.status = Scan.DONE
    scan_object.end_time = timezone.now()
    scan_object.save()
    # TODO: Check reason for if it was finished, cancelled, or shutdown
    reactor.stop()

def handle_error(failure, response, spider):
    log.msg("Scan failed: %s" % failure.getErrorMessage(), level=log.ERROR)
    scan_object = Scan.objects.get(pk=scan_id)
    scan_object.status = Scan.FAILED
    scan_object.end_time = timezone.now()
    scan_object.reason = failure.getErrorMessage()
    scan_object.save()

spider = ScannerSpider(scan_id=scan_id)
settings = get_project_settings()
crawler = Crawler(settings)
crawler.signals.connect(handle_closed, signal=signals.spider_closed)
crawler.signals.connect(handle_error, signal=signals.spider_error)
crawler.configure()
crawler.crawl(spider)
crawler.start()
log.start()
reactor.run() # the script will block here until the spider_closed signal was sent