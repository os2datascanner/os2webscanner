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
"""Unit tests for OS2Webscanner.

These will pass when you run "manage.py test os2webscanner".
"""

import os
import pep8
from django.test import TestCase
from django.conf import settings

from .models.domains.webdomain_model import WebDomain
from .models.organization_model import Organization
from .models.scannerjobs.webscanner_model import WebScanner
from .models.scans.scan_model import Scan
from .validate import validate_domain


class ScannerTest(TestCase):

    """Test running a scan and domain validation."""
    # TODO: Capture the interaction so these tests can work without an
    # Internet connection! !!!

    @classmethod
    def setUpTestData(cls):
        """Setup some data to test with."""
        # Don't change the order of these, because Magenta needs
        # pk = 2 to pass the validation test
        cls.magenta = Organization(name="Magenta", pk=1)
        cls.magenta.save()
        cls.google = Organization(name="Google", pk=2)
        cls.google.save()

    def test_validate_domain(self):
        """Test validating domains."""
        # Make sure Google does not validate in any of the possible methods
        all_methods = [WebDomain.WEBSCANFILE, WebDomain.METAFIELD]
        # Make sure Magenta's website validates using all possible methods
        # Magenta's website is under re-construction.
        """for validation_method in [WebDomain.WEBSCANFILE, WebDomain.METAFIELD]:
            domain = WebDomain(url="http://www.magenta.dk/",
                            validation_method=validation_method,
                            organization=self.magenta,
                            pk=1)
            domain.save()
            print("VALIDATING", validation_method)
            self.assertTrue(validate_domain(domain))"""

        for validation_method in all_methods:
            domain = WebDomain(url="http://www.google.com/",
                            validation_method=validation_method,
                            organization=self.google,
                            pk=2)
            domain.save()
            self.assertFalse(validate_domain(domain))

    def test_run_scan(self):
        """Test running a scan."""
        domain = WebDomain(url="http://www.magenta.dk/",
                        organization=self.magenta,
                        validation_method=WebDomain.ROBOTSTXT,
                        validation_status=1)
        scanner = WebScanner(organization=self.magenta, schedule="")
        scanner.save()
        domain.save()
        scanner.domains.add(domain)
        self.assertTrue(isinstance(scanner.run('kaflaflibob'), Scan))
        self.assertFalse(isinstance(scanner.run('kaflaflibob'), Scan))


# TODO: Make it pep8 version 1.7 compatible
def pep8_test(filepath):
    """Run a pep8 test on the filepath."""
    def do_test(self):
        # print "PATH:", filepath
        # arglist = ['--exclude=lib,migrations', filepath]
        pep8styleguide = pep8.StyleGuide(
            exclude=['lib', 'migrations'],
            filename=['*.py'],
            filepath=filepath,
            show_pep8=False,
            show_source=False,
        )
        pep8styleguide.input_dir(filepath)
        basereport = pep8.BaseReport(benchmark_keys={})
        output = basereport.get_statistics(prefix='')
        # print "PEP8 OUTPUT: " + str(output)
        self.assertEqual(len(output), 0)

    return do_test

