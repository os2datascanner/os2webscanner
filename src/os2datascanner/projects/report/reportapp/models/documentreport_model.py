from django.db import models
from django.contrib.postgres.fields import JSONField


class DocumentReport(models.Model):
    path = models.CharField(max_length=2000, verbose_name="Path")
    # It could be that the meta data should not be part of the jsonfield...
    data = JSONField(null=True)

    def _str_(self):
        return self.path

    class Meta:
        verbose_name_plural = "Document reports"
