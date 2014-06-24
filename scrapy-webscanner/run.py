#!/usr/bin/env python
import os
import sys

# Include the Django model
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"

from twisted.internet import reactor
from scrapy.crawler import Crawler
from scrapy import log, signals
from scrapy.utils.project import get_project_settings
from scanner.spiders.scanner import ScannerSpider

spider = ScannerSpider(url='http://www.magenta.dk', sitemap_urls=['http://www.magenta-aps.dk/sitemap.xml'], allowed_domains=['magenta.dk'])
settings = get_project_settings()
crawler = Crawler(settings)
crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
crawler.configure()
crawler.crawl(spider)
crawler.start()
log.start()
reactor.run() # the script will block here until the spider_closed signal was sent