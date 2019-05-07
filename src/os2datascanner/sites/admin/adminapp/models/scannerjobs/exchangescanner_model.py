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
from django.db import models

from ..domains.exchangedomain_model import ExchangeDomain
from .scanner_model import Scanner


class ExchangeScanner(Scanner):

    """File scanner for scanning network drives and folders"""
    # TODO: ExchangeScanner should only be able to have one domain attached
    domains = models.ManyToManyField(ExchangeDomain, related_name='exchangedomains',
                                     verbose_name='Exchangedomæner')

    is_exporting = models.BooleanField(default=False)

    # If nothing has been exported yet this property is false.
    is_ready_to_scan = models.BooleanField(default=False)

    def get_type(self):
        return 'exchange'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/exchangescanners/'

    def create_scan(self):
        return super().create_scan()

    class Meta:
        db_table = 'os2webscanner_exchangescanner'
