import scrapy
from scrapy import signals
from scrapy.crawler import CrawlerProcess
from os2datascanner.engine.scanners.spiders.scanner_spider import ScannerSpider


class MySpider(scrapy.Spider):

    name = 'blogscan'
    allowed_domains = ['magenta-aps.dk']

    def start_requests(self):
        yield scrapy.Request('http://blog.magenta-aps.dk', self.parse)

    def parse(self, response):
        print('A response from %s just arrived!' % response.url)


def response_received(response, request, spider):
    print('Response_received: A response from %s just arrived!' % response.url)


def engine_started():
    print('Engine started.')


def spider_opened(spider):
    print('Spider opened.')


def spider_error(failure, response, spider):
    print('Spider error.')


if __name__ == '__main__':
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
    })

    crawler = process.create_crawler(ScannerSpider())
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
