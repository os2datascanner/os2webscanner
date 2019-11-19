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


from .rule_model import Rule


class AddressRule(Rule):
    DATABASE_PD_2015 = 0

    database_choices = (
        (DATABASE_PD_2015, u'Post Danmarks liste over gadenavne pr. ca. 1. januar 2015'),
    )

    database = models.IntegerField(
            choices=database_choices,
            default=DATABASE_PD_2015,
            verbose_name="Gadenavnedatabase")

    whitelist = models.TextField(blank=True,
                                 default="",
                                 verbose_name='Godkendte adresser')
    blacklist = models.TextField(blank=True,
                                 default="",
                                 verbose_name='Sortlistede adresser')

    def make_engine2_rule(self):
        # engine2 doesn't have address rules yet
        raise NotImplementedError("AddressRule.make_engine2_rule")
