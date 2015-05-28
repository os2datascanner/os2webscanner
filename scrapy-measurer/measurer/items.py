# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
import hashlib

class MeasurerItem(scrapy.Item):
    mimetype = scrapy.Field()
    filename = scrapy.Field()
    content = scrapy.Field()
    length = scrapy.Field()
    md5 = scrapy.Field()
    from_conversion = scrapy.Field()
    conversion_time = scrapy.Field()

    def __init__(self):
        super(MeasurerItem, self).__init__()
        self['mimetype'] = 'application/octet-stream'
        self['from_conversion'] = False
        self['conversion_time'] = 0.0
        self.set_content("")
        self['filename'] = "dummy"


    def set_content(self, content):
        self['content'] = content
        self['length'] = len(content)
        self['md5'] = hashlib.md5(content).hexdigest()
