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
import urllib

from django.conf import settings
from django.db import models

from ..scans.webscan_model import WebScan
from .scanner_model import Scanner


class WebScanner(Scanner):

    """Web scanner for scanning websites."""

    linkable = True

    do_link_check = models.BooleanField(default=False,
                                        verbose_name='Tjek links')
    do_external_link_check = models.BooleanField(
        default=False,
        verbose_name='Eksterne links'
    )
    do_last_modified_check_head_request = models.BooleanField(
        default=True,
        verbose_name='Brug HTTP HEAD-forespørgsler'
    )
    do_collect_cookies = models.BooleanField(
        default=False,
        verbose_name='Saml cookies'
    )

    ROBOTSTXT = 0
    WEBSCANFILE = 1
    METAFIELD = 2

    validation_method_choices = (
        (ROBOTSTXT, 'robots.txt'),
        (WEBSCANFILE, 'webscan.html'),
        (METAFIELD, 'Meta-felt'),
    )

    validation_method = models.IntegerField(choices=validation_method_choices,
                                            default=ROBOTSTXT,
                                            verbose_name='Valideringsmetode')

    sitemap = models.FileField(upload_to='sitemaps',
                               blank=True,
                               verbose_name='Sitemap Fil')

    sitemap_url = models.CharField(max_length=2048,
                                   blank=True,
                                   default="",
                                   verbose_name='Sitemap URL')

    download_sitemap = models.BooleanField(default=True,
                                           verbose_name='Hent Sitemap fra '
                                                        'serveren')

    @property
    def display_name(self):
        """The name used when displaying the domain on the web page."""
        return "Domain '%s'" % self.root_url

    @property
    def root_url(self):
        """Return the root url of the domain."""
        url = self.url.replace('*.', '')
        if (not self.url.startswith('http://') and not
        self.url.startswith('https://')):
            return 'http://%s/' % url
        else:
            return url

    @property
    def sitemap_full_path(self):
        """Get the absolute path to the uploaded sitemap.xml file."""
        return "%s/%s" % (settings.MEDIA_ROOT, self.sitemap.url)

    @property
    def default_sitemap_path(self):
        return "/sitemap.xml"

    def get_sitemap_url(self):
        """Get the URL of the sitemap.xml file.

        This will be the URL specified by the user, or if not present, the
        URL of the default sitemap.xml file.
        If downloading of the sitemap.xml file is disabled, this will return
        None.
        """
        if not self.download_sitemap:
            return None
        else:
            sitemap_url = self.sitemap_url or self.default_sitemap_path
            return urllib.parse.urljoin(self.root_url, sitemap_url)

    def create_scan(self):
        return WebScan().create(self)

    def get_type(self):
        return 'web'

    def get_absolute_url(self):
        """Get the absolute URL for scanners."""
        return '/webscanners/'
