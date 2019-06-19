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
from io import StringIO

from django.db import models

from .scan_model import Scan


class WebScan(Scan):

    """An actual instance of the web scanning process done by a web scanner."""

    def __init__(self, *args, **kwargs):
        """Initialize a new scan.

        Stores the old status of the scan for later use.
        """
        super().__init__(*args, **kwargs)
        self._old_status = self.status

    do_link_check = models.BooleanField(default=False,
                                        verbose_name='Tjek links')

    do_external_link_check = models.BooleanField(
        default=False,
        verbose_name='Tjek eksterne links'
    )

    do_last_modified_check_head_request = models.BooleanField(
        default=True,
        verbose_name='Brug HTTP HEAD-forespørgsler',
        help_text='Tjek datoer ved hjælp af en særskilt forespørgsel',
    )

    do_collect_cookies = models.BooleanField(default=False,
                                             verbose_name='Opsaml cookies')

    # Create method - copies fields from scanner
    def create(self, scanner):
        """ Create and copy fields from scanner. """
        self.do_link_check = scanner.do_link_check
        self.do_external_link_check = scanner.do_external_link_check
        self.do_last_modified_check_head_request = scanner.do_last_modified_check_head_request
        self.do_collect_cookies = scanner.do_collect_cookies
        return super().create(scanner)

        # Cookie log - undigested cookie strings for inspection.
    def log_cookie(self, string):
        with open(self.cookie_log_file, "a") as f:
            f.write("{0}\n".format(string))

    @property
    def no_of_cookies(self):
        try:
            with open(self.cookie_log_file, "r") as f:
                return sum(1 for line in f)
        except IOError:
            return 0

    @property
    def cookie_log(self):
        try:
            with open(self.cookie_log_file, "r") as f:
                raw_log = f.read()
        except IOError:
            return ""

        cookie_counts = {}
        lines = raw_log.split('\n')
        for l in lines:
            if not l:
                continue
            domain = l.split('|')[0]
            cookie = l.split('|')[1]
            if domain in cookie_counts:
                if cookie in cookie_counts[domain]:
                    cookie_counts[domain][cookie] += 1
                else:
                    cookie_counts[domain][cookie] = 1
            else:
                cookie_counts[domain] = {cookie: 1}

        output = StringIO.StringIO()
        for domain in cookie_counts:
            output.write("{0}\n".format(domain))
            for cookie in cookie_counts[domain]:
                output.write("    {0} Antal: {1}\n".format(
                    cookie,
                    cookie_counts[domain][cookie]
                ))

        result = output.getvalue()

        output.close()
        return result

    @property
    def cookie_log_file(self):
        """Return the file path to this scan's cookie log."""
        return os.path.join(self.scan_log_dir, 'cookie_%s.log' % self.pk)

    @property
    def no_of_broken_links(self):
        """Return the number of broken links for this scan."""
        return self.urls.exclude(status_code__isnull=True).count()

    @property
    def has_active_scans(self, scanner):
        """Whether the scanner has active scans."""
        active_scanners = WebScan.objects.filter(scanner=scanner, status__in=(
                Scan.NEW, Scan.STARTED)).count()
        return active_scanners > 0

    class Meta:
        db_table = 'os2webscanner_webscan'
