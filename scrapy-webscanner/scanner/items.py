"""Scrapy Items."""

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field
from scrapy.contrib.djangoitem import DjangoItem
from os2webscanner.models import *


class MatchItem(DjangoItem):

    """Scrapy Item using the Match object from the Django model as storage."""

    django_model = Match
