# -*- coding: UTF-8 -*-
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

from .group_model import Group
from .organization_model import Organization
from .sensitivity_level import Sensitivity


class RegexRule(models.Model):

    """Represents matching rules based on regular expressions."""

    name = models.CharField(max_length=256, unique=True, null=False,
                            verbose_name='Navn')
    organization = models.ForeignKey(Organization, null=False,
                                     verbose_name='Organisation')
    group = models.ForeignKey(Group, null=True, blank=True,
                              verbose_name='Gruppe')
    match_string = models.CharField(max_length=1024, blank=False,
                                    verbose_name='Udtryk')

    description = models.TextField(verbose_name='Beskrivelse')
    sensitivity = models.IntegerField(choices=Sensitivity.choices,
                                      default=Sensitivity.HIGH,
                                      verbose_name='Følsomhed')

    @property
    def display_name(self):
        """The name used when displaying the regexrule on the web page."""
        return "Regel '%s'" % self.name

    def get_absolute_url(self):
        """Get the absolute URL for rules."""
        return '/rules/'

    def __unicode__(self):
        """Return the name of the rule."""
        return self.name

    def __str__(self):
        """
        Returns a string object repreesentation of this object
        :return:
        """
        return '{\n\tname: ' + self.name + \
               ',\n\torganization_id: '+ self.organization.name +\
               ',\n\tmatch_string: ' + self.match_string + '\n}'
