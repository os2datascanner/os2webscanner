from django.db import models

from .organization_model import Organization


class Md5Sum(models.Model):

    """"Store MD5 sums of binary files to avoid reprocessing."""

    organization = models.ForeignKey(Organization,
                                     null=False,
                                     verbose_name='Organisation')
    md5 = models.CharField(max_length=32, null=False, blank=False)
    is_cpr_scan = models.BooleanField()
    is_check_mod11 = models.BooleanField()
    is_ignore_irrelevant = models.BooleanField()

    class Meta:
        unique_together = ('md5', 'is_cpr_scan', 'is_check_mod11',
                           'is_ignore_irrelevant', 'organization')

    def __unicode__(self):
        return u"{0}: {1}".format(self.organization.name, self.md5)
