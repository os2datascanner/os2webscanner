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

"""The Django model for Rulses set."""

from django.db import models
from .organization_model import Organization
from .regexrule_model import RegexRule
from .sensitivity_level import Sensitivity


class RulesSet(models.Model):
    """
    This model represents the rule set that relates list of rules to a single scan job.
    See: https://redmine.magenta-aps.dk/issues/22651
    """
    name = models.CharField(max_length=256, unique=True, null=False,
                            verbose_name='Navn')

    organization = models.ForeignKey(Organization, null=True,
                                     verbose_name='Organisation')

    description = models.TextField(verbose_name='Beskrivelse', default='')

    regexrules = models.ManyToManyField(RegexRule, null=False)

    sensitivity = models.IntegerField(choices=Sensitivity.choices,
                                      default=Sensitivity.HIGH,
                                      verbose_name='Følsomhed')
