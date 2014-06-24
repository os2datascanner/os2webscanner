# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy import log
from scrapy.exceptions import DropItem

class MatchSaverPipeline(object):
    def process_item(self, item, spider):
        # TODO: Save match to Django DB
        # item.save()
        log.msg("Match: " + str(item))
        return item