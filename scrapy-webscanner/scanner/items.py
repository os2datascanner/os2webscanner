# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field
from scrapy.contrib.djangoitem import DjangoItem
from os2webscanner.models import *

class MatchItem(DjangoItem):
    django_model = Match

class UrlItem(DjangoItem):
    django_model = Url

class ScanItem(DjangoItem):
    django_model = Scan

