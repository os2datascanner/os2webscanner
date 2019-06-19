from django.db import models
from urllib.request import urlopen

from .scans.webscan_model import WebScan


class ReferrerUrl(models.Model):

    """A representation of a referrer URL."""

    class Meta:
        verbose_name = 'Referer URL'

    url = models.CharField(max_length=2048, verbose_name='URL')
    scan = models.ForeignKey(
        WebScan,
        null=False,
        verbose_name='Scan',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        """Return the URL."""
        return self.url

    @property
    def content(self):
        """Return the content of the target url"""
        try:
            file = urlopen(self.url)
            return file.read()
        except Exception as e:
            return str(e)

    @property
    def broken_urls(self):
        result = self.os2webscanner_webversion_linked_urls.exclude(
            status_code__isnull=True
        ).order_by('url')

        return result
        # .filter(status=None)
        # WebVersion.objects.filter(referrerurls__contains=self, status=None)
