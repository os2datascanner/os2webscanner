"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import os
import pep8

from django.test import TestCase
from django.conf import settings

from os2webscanner.models import Domain, Organization, Scanner
from validate import validate_domain

install_directory = os.path.abspath(os.path.join(settings.BASE_DIR, '..'))


class ScannerTest(TestCase):
    @classmethod
    def setUpClass(cls):
        # Don't change the order of these, because Magenta needs pk = 2 to pass
        # the validation test
        cls.google = Organization(name="Google")
        cls.google.save()
        cls.magenta = Organization(name="Magenta", pk=2)
        cls.magenta.save()

    def test_validate_domain(self):
        # Make sure Google does not validate in any of the possible methods
        all_methods = [Domain.ROBOTSTXT, Domain.WEBSCANFILE, Domain.METAFIELD]
        for validation_method in all_methods:
            domain = Domain(url="http://www.google.com/",
                            validation_method=validation_method,
                            organization=self.google)
            domain.save()
            self.assertFalse(validate_domain(domain))

        # Make sure Magenta's website validates using all possible methods
        for validation_method in all_methods:
            domain = Domain(url="http://www.magenta.dk/",
                            validation_method=validation_method,
                            organization=self.magenta)
            domain.save()
            self.assertTrue(validate_domain(domain))

    def test_run_scan(self):
        domain = Domain(url="http://www.magenta.dk/",
                        organization=self.magenta,
                        validation_method=Domain.ROBOTSTXT)
        scanner = Scanner(organization=self.magenta, schedule="")
        scanner.save()
        self.assertTrue(scanner.run(test_only=True))
        self.assertFalse(scanner.run(test_only=True))


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


def pep8_test(filepath):
    def do_test(self):
        # print "PATH:", filepath
        arglist = ['--exclude=lib', filepath]
        pep8.process_options(arglist)
        pep8.input_dir(filepath)
        output = pep8.get_statistics()
        # print "PEP8 OUTPUT: " + str(output)
        self.assertEqual(len(output), 0)

    return do_test


class Pep8Test(TestCase):
    """Test that the template system a well as the default clients and plugins
    are PEP8-compliant."""
    j = lambda dir: os.path.join(install_directory, dir)

    test_os2webscanner = pep8_test(j('django-os2webscanner'))
    test_scrapywebscanner = pep8_test(j('scrapy-webscanner'))
