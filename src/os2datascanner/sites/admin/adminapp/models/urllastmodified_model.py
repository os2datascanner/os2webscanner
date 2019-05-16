from django.db import models

from .scannerjobs.scanner_model import Scanner


class UrlLastModified(models.Model):

    """A representation of a URL, its last-modifed date, and its links."""

    class Meta:
        verbose_name = 'Last modified URL'

        unique_together = (
            ('url', 'scanner'),
        )

    url = models.CharField(max_length=2048, verbose_name='Url')
    last_modified = models.DateTimeField(blank=True, null=True,
                                         verbose_name='Last-modified')
    links = models.ManyToManyField("self", symmetrical=False,
                                   verbose_name='Links')
    scanner = models.ForeignKey(
        Scanner,
        null=False,
        verbose_name='WebScanner',
        on_delete=models.CASCADE,
    )

    def __unicode__(self):
        """Return the URL and last modified date."""
        return "<%s %s>" % (self.url, self.last_modified)

    def __str__(self):
        """Return the URL and last modified date."""
        return "<%s %s>" % (self.url, self.last_modified)
