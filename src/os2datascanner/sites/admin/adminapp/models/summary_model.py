# encoding: utf-8
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )

from django.db import models
from recurrence.fields import RecurrenceField

from .group_model import Group
from .organization_model import Organization
from .userprofile_model import UserProfile
from .scannerjobs.webscanner_model import WebScanner


class Summary(models.Model):

    """The necessary configuration for summary reports."""

    name = models.CharField(max_length=256, unique=True, null=False,
                            verbose_name='Navn')
    description = models.TextField(verbose_name='Beskrivelse', null=True,
                                   blank=True)
    schedule = RecurrenceField(max_length=1024,
                               verbose_name='Planlagt afvikling')
    last_run = models.DateTimeField(blank=True, null=True,
                                    verbose_name='Sidste kørsel')
    recipients = models.ManyToManyField(UserProfile, blank=True,
                                        verbose_name="Modtagere")
    scanners = models.ManyToManyField(WebScanner, blank=True,
                                      verbose_name="Scannere")
    organization = models.ForeignKey(Organization, null=False,
                                     verbose_name='Organisation',
                                     on_delete=models.PROTECT)
    group = models.ForeignKey(Group, null=True, blank=True,
                              verbose_name='Gruppe',
                              on_delete=models.SET_NULL)
    do_email_recipients = models.BooleanField(default=False,
                                              verbose_name="Udsend mails")

    def __unicode__(self):
        """Return the name as a text representation of this summary object."""
        return self.name

    @property
    def display_name(self):
        """Display name = name."""
        return self.name

    class Meta:
        ordering = ['name', ]
