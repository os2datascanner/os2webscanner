#!/usr/bin/env python
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

"""Unit tests for the scanner."""

# Include the Django app
import os
import sys
import shutil
import tempfile

base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"

import django
django.setup()

import re

import linkchecker

import unittest
from scanner.rules import cpr, name
from scanner.spiders import scanner_spider
from scanner.processors import pdf, libreoffice, html

from os2webscanner.models.conversionqueueitem_model import ConversionQueueItem
from os2webscanner.models.url_model import Url
from os2webscanner.models.scan_model import Scan


class FileExtractorTest(unittest.TestCase):

    def test_file_extractor(self):
        with tempfile.TemporaryDirectory(dir=base_dir + '/scrapy-webscanner/tests/data/') as temp_dir:
            filepath1 = temp_dir + '/kk.dk'
            filepath2 = temp_dir + '/æøå'
            os.mkdir(filepath1)
            os.mkdir(filepath2)

            filemap = scanner_spider.ScannerSpider.file_extractor(self, 'file://' + temp_dir)

            encoded_file_path1 = filemap[0].encode('utf-8')
            encoded_file_path2 = filemap[1].encode('utf-8')

            self.assertEqual(filepath1, encoded_file_path1.decode('utf-8').replace('file://', ''))
            self.assertEqual(filepath2, encoded_file_path2.decode('utf-8').replace('file://', ''))


class ExternalLinkCheckerTest(unittest.TestCase):

    """Test the external link checker."""

    def test_checker(self):
        """Test the link checker."""
        # Google should be OK
        self.assertIsNone(linkchecker.check_url(
            "http://www.google.com/"))

        # Test 404 error
        res = linkchecker.check_url(
            "http://google.com/asdasdfasdgfr4rter.html")
        self.assertIsNotNone(res)
        # Check status code is correct
        self.assertEqual(res["status_code"], 404)

        # Random domain is not OK
        self.assertIsNotNone(linkchecker.check_url(
            "http://asdfasdfasdf324afddsfasdf/"))


class NameTest(unittest.TestCase):

    """Test the name rule."""

    def test_matching(self):
        """Test Name matching in text."""
        text = """
            Jens Jensen
            Jim Smith Jones
            sdfsdsad Asdfsddsfasd
            Lars L. Larsen
            Lars Lars Lars Larsen
            James Thomas Jones Smith
            """
        # whitelist = """
        # Jim Smiths
        # """
        valid_names = ['Jens Jensen', 'Jim Smith Jones',
                       'Lars L. Larsen', 'Lars Lars Lars Larsen']
        invalid_names = ['sdfsdsad Asdfsddsfasd']
        matches = name.NameRule().execute(text)
        matches = [re.sub('\s+', ' ', m['matched_data']) for m in matches]
        print(matches)
        for valid_name in valid_names:
            self.assertTrue(any(m == valid_name for m in matches),
                            valid_name + " is valid")
        for invalid_name in invalid_names:
            self.assertFalse(any(m == invalid_name for m in matches),
                             invalid_name + " is valid")


class CPRTest(unittest.TestCase):

    """Test the CPR rule."""

    def check_matches(self, matches, valid_matches, invalid_matches):
        """Check that the matches contains the given valid matches and none
        of the given invalid matches."""
        print(matches)
        for valid_match in valid_matches:
            self.assertTrue(
                any(m['matched_data'] == valid_match for m in matches))
        for invalid_match in invalid_matches:
            self.assertFalse(
                any(m['matched_data'] == invalid_match for m in matches))

    def test_matching(self):
        """Test CPR matching in text."""
        text = """
            211062-5629
            4110625629
            6113625629
            911062 5629
            2006359917            
            211062-5629 # in the past
            200638-5322 # in the future
            080135-5102 # in the future
            21 10 62 - 3308
            """
        valid_cprs = ['2110625629', '2006359917', '2006385322', '2110625629',
                      '0801355102', '2110623308']
        invalid_cprs = ['4110625629', '2113625629', '9110625629']

        matches = cpr.match_cprs(text, mask_digits=False,
                                 ignore_irrelevant=False)
        self.check_matches(matches, valid_cprs, invalid_cprs)

    def test_matching_ignore_irrelevant(self):
        """Test CPR matching in text."""
        text = """
            211062-0155 # current
            211062-5629 # in the past
            200638-5322 # in the future
            080135-5102 # in the future
            """
        valid_cprs = ['2110620155']
        invalid_cprs = ['2110625629', '2006385322', '0801355102']

        matches = cpr.match_cprs(text, mask_digits=False,
                                 ignore_irrelevant=True)
        self.check_matches(matches, valid_cprs, invalid_cprs)

    def test_modulus11_check(self):
        # Check that modulus 11 check works
        self.assertTrue(cpr.modulus11_check("2110625629"))
        self.assertFalse(cpr.modulus11_check("2110625628"))

        # Check that modulus 11 check PASSES for exception dates even though
        # they have an invalid check digit.
        self.assertTrue(cpr.modulus11_check("0101650123"))
        self.assertTrue(cpr.modulus11_check("0101660123"))


class PDF2HTMLTest(unittest.TestCase):

    test_dir = base_dir + '/scrapy-webscanner/tests/data/'

    def create_ressources(self, filename):
        shutil.copy2(self.test_dir + 'pdf/' + filename, self.test_dir + 'tmp/')
        url = Url(scan=Scan(), url=self.test_dir + 'tmp/' + filename)
        item = ConversionQueueItem(url=url,
                                   file=self.test_dir + 'tmp/' + filename,
                                   type=pdf.PDFProcessor,
                                   status=ConversionQueueItem.NEW)

        with tempfile.TemporaryDirectory(dir=self.test_dir + 'tmp/') as temp_dir:
            result = pdf.PDFProcessor.convert(self, item, temp_dir)

        return result

    def test_pdf2html_conversion_success(self):
        filename = 'Midler-til-frivilligt-arbejde.pdf'
        result = self.create_ressources(filename)

        self.assertEqual(result, True)

    def test_pdf2html_data_protection_bit(self):
        filename = 'Tilsynsrapport (2013) - Kærkommen.PDF'
        result = self.create_ressources(filename)

        self.assertEqual(result, True)

    def test_pdf2html_find_cpr_number(self):
        filename = 'somepdf.pdf'
        result = self.create_ressources(filename)

        self.assertEqual(result, True)


class LibreofficeTest(unittest.TestCase):

    test_dir = base_dir + '/scrapy-webscanner/tests/data/'

    def create_ressources(self, filename):
        shutil.copy2(self.test_dir + 'libreoffice/' + filename, self.test_dir + 'tmp/')
        url = Url(scan=Scan(), url=self.test_dir + 'tmp/' + filename)
        item = ConversionQueueItem(url=url,
                                   file=self.test_dir + 'tmp/' + filename,
                                   type=libreoffice.LibreOfficeProcessor,
                                   status=ConversionQueueItem.NEW)

        with tempfile.TemporaryDirectory(dir=self.test_dir + 'tmp/') as temp_dir:
            libreoffice_processor = libreoffice.LibreOfficeProcessor()
            libreoffice_processor.set_home_dir(self.test_dir + 'libreoffice/home_dir/')
            result = libreoffice_processor.convert(item, temp_dir)

        return result

    def test_libreoffice_conversion_success(self):
        filename = 'KK SGP eksempel 2013.02.27.xls'
        result = self.create_ressources(filename)
        self.assertEqual(result, True)


class HTMLTest(unittest.TestCase):

    test_dir = base_dir + '/scrapy-webscanner/tests/data/'

    def create_ressources(self, filename):
        shutil.copy2(self.test_dir + 'html/' + filename, self.test_dir + 'tmp/')
        url = Url(scan=Scan(), url=self.test_dir + 'tmp/' + filename)
        item = ConversionQueueItem(url=url,
                                   file=self.test_dir + 'tmp/' + filename,
                                   type=html.HTMLProcessor,
                                   status=ConversionQueueItem.NEW)

        return item

    def test_html_process_method(self):
        """Test case used to investigate UTF-8 decoding fail error.
         Will always return false as text processor instantiates scanner object which makes db call."""
        filename = 'Midler-til-frivilligt-arbejde.html'
        item = self.create_ressources(filename)
        html_processor = html.HTMLProcessor()
        result = html_processor.handle_queue_item(item)
        self.assertEqual(result, False)


def main():
    """Run the unit tests."""
    unittest.main()


if __name__ == '__main__':
    main()
