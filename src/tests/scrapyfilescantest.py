import sys
import os
import datetime
import scrapy
from scrapy import signals
from scrapy.crawler import CrawlerProcess
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(os.path.join(__file__, "../"))))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "os2datascanner.projects.admin.settings"

import django
django.setup()

data_dir = base_dir + '/scrapy-webscanner/tests/data/'


class MySpider(scrapy.Spider):

    name = 'filescan'
    allowed_domains = [data_dir]

    def start_requests(self):
        yield scrapy.Request('file://' + data_dir + 'somepdf.pdf', self.parse)

    def parse(self, response):
        last_modified_date = datetime.datetime.fromtimestamp(
            os.path.getmtime(response.url.replace('file://', '')))
        print('A response from %s just arrived!' % last_modified_date)


def response_received(response, request, spider):
    print('Response_received: A response from %s just arrived!' % response.url)


def engine_started():
    print('Engine started.')


def spider_opened(spider):
    print('Spider opened.')


def spider_error(failure, response, spider):
    print('Spider error.')


def main():
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
    })

    crawler = process.create_crawler(MySpider)
    crawler.signals.connect(response_received,
                            signal=signals.response_received)
    crawler.signals.connect(engine_started,
                            signal=signals.engine_started)
    crawler.signals.connect(spider_opened,
                            signal=signals.spider_opened)
    crawler.signals.connect(spider_error,
                            signal=signals.spider_error)
    #crawler.crawl()
    #import pdb; pdb.set_trace()
    process.crawl(crawler)
    process.start()


if __name__ == '__main__':
    main()
