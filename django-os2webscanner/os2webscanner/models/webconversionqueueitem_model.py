from django.db import models

from conversionqueueitem_model import ConversionQueueItem
from weburl_model import WebUrl


class WebConversionQueueItem(ConversionQueueItem):
    url = models.ForeignKey(WebUrl, null=False, verbose_name='Url')
