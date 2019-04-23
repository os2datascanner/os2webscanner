# -*- coding: utf-8 -*-
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

import re

from django.db import models

from ..authentication_model import Authentication
from ..group_model import Group
from ..organization_model import Organization


class Domain(models.Model):

    """Represents a domain to be scanned."""

    # CONCRETE_CLASSES = ('webdomain', 'filedomain',)

    # Validation status

    VALID = 1
    INVALID = 0

    validation_choices = (
        (INVALID, "Ugyldig"),
        (VALID, "Gyldig"),
    )

    url = models.CharField(max_length=2048, verbose_name='Url')

    authentication = models.OneToOneField(Authentication,
                                          null=True,
                                          related_name='%(app_label)s_%(class)s_authentication',
                                          verbose_name='Brugernavn')

    organization = models.ForeignKey(Organization,
                                     null=False,
                                     related_name='%(app_label)s_%(class)s_organization',
                                     verbose_name='Organisation')

    group = models.ForeignKey(Group,
                              null=True,
                              blank=True,
                              related_name='%(app_label)s_%(class)s_groups',
                              verbose_name='Gruppe')

    validation_status = models.IntegerField(choices=validation_choices,
                                            default=INVALID,
                                            verbose_name='Valideringsstatus')

    exclusion_rules = models.TextField(blank=True,
                                       default="",
                                       verbose_name='Ekskluderingsregler')
    @property
    def display_name(self):
        """The name used when displaying the domain on the web page."""
        return "Domain '%s'" % self.url

    def exclusion_rule_list(self):
        """Return the exclusion rules as a list of strings or regexes."""
        REGEX_PREFIX = "regex:"
        rules = []
        for line in self.exclusion_rules.splitlines():
            line = line.strip()
            if line.startswith(REGEX_PREFIX):
                rules.append(re.compile(line[len(REGEX_PREFIX):],
                                        re.IGNORECASE))
            else:
                rules.append(line)
        return rules

    def get_absolute_url(self):
        """Get the absolute URL for domains."""
        return '/domains/'

    def __unicode__(self):
        """Return the URL for the domain."""
        return self.url

    def __str__(self):
        """Return the URL for the domain."""
        return self.url
