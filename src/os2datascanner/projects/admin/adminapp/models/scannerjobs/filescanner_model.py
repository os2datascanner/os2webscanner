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
import os
import tempfile
from pathlib import PureWindowsPath
from subprocess import call

import structlog
from django.conf import settings
from django.db import models

from os2datascanner.engine2.model.smbc import SMBCSource
from .scanner_model import Scanner

# Get an instance of a logger
logger = structlog.get_logger()

class FileScanner(Scanner):

    """File scanner for scanning network drives and folders"""


    alias = models.CharField(max_length=64, verbose_name='Drevbogstav', null=True)

    @property
    def root_url(self):
        """Return the root url of the domain."""
        url = self.url.replace('*.', '')
        return url

    def __str__(self):
        """Return the URL for the scanner."""
        return self.url

    def path_for(self, path):
        root_url = (
            self.url if self.url.startswith('file:')
            else PureWindowsPath(self.url).as_uri()
        )

        if path.startswith(root_url):
            return str(
                PureWindowsPath(self.alias + ':\\') / path[len(root_url):]
            )

        return path

    def get_type(self):
        return 'file'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/filescanners/'

    def make_engine2_source(self):
        return SMBCSource(
                self.url,
                user=self.authentication.username,
                password=self.authentication.get_password(),
                domain=self.authentication.domain)
