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

from .scanner_model import Scanner
from ..domains.webdomain_model import WebDomain


class WebScanner(Scanner):

    """Web scanner for scanning websites."""

    domains = models.ManyToManyField(WebDomain, related_name='webdomains',
                                     verbose_name='Web Domæner')

    do_link_check = models.BooleanField(default=False,
                                        verbose_name='Tjek links')
    do_external_link_check = models.BooleanField(
        default=False,
        verbose_name='Eksterne links'
    )
    do_last_modified_check_head_request = models.BooleanField(
        default=True,
        verbose_name='Brug HTTP HEAD request'
    )
    do_collect_cookies = models.BooleanField(
        default=False,
        verbose_name='Saml cookies'
    )

    def create_scan(self):
        from ..scans.webscan_model import WebScan
        webscan = WebScan()
        return webscan.create(self)

    def get_type(self):
        return 'web'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/webscanners/'

    class Meta:
        db_table = 'os2webscanner_webscanner'
