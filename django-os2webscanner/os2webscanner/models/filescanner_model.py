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
from .filedomain_model import FileDomain


class FileScanner(Scanner):

    """File scanner for scanning network drives and folders"""

    domains = models.ManyToManyField(FileDomain, related_name='filedomains',
                                     verbose_name='Fil Domæner')

    def create_scan(self):
        """
        Creates a file scan.
        :return: A file scan object
        """
        # hvad kan gå galt: mount fejler, login er forkert,
        # login mangler, login skal slet ikke være der, stien til netværksdrev er forkert.
        for domain in self.domains.all():
            if domain.url == "//sparketilhjørne":
                pass
            elif not domain.smbmount():
                return FileDomain.MOUNT_FAILED

        from .filescan_model import FileScan
        return FileScan.create(self)

    def get_type(self):
        return 'file'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/filescanners/'

    class Meta:
        db_table = 'os2webscanner_filescanner'
