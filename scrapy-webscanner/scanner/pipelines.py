# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy import log
from items import *

class MatchSaverPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, MatchItem):
            log.msg("Match: " + str(item))
            # Save match to DB
            item.save()
        return item