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
import datetime
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import django
import lxml
import requests

from os2datascanner.engine.utils import run_django_setup

run_django_setup()

test_dir = Path(__file__).parent
data_dir = test_dir.joinpath('data')
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

from os2datascanner.engine import linkchecker
from os2datascanner.engine.scanners.scanner_types.scanner import Scanner
from os2datascanner.engine.scanners.spiders.filespider import FileSpider
from os2datascanner.engine.scanners.scanner_types.filescanner import FileScanner

from os2datascanner.engine.scanners.rules import cpr, name, regexrule

from os2datascanner.engine.scanners.processors import pdf, libreoffice, html, zip

from os2datascanner.projects.admin.adminapp.models.version_model import Version
from os2datascanner.projects.admin.adminapp.models.location_model import Location


from os2datascanner.projects.admin.adminapp.models.conversionqueueitem_model import ConversionQueueItem

from os2datascanner.projects.admin.adminapp.models.scans.scan_model import Scan
from os2datascanner.projects.admin.adminapp.models.scans.webscan_model import WebScan
from os2datascanner.projects.admin.adminapp.models.scannerjobs.webscanner_model import WebScanner

from os2datascanner.projects.admin.adminapp.models.rules.regexrule_model import RegexRule
from os2datascanner.projects.admin.adminapp.models.rules.namerule_model import NameRule
from os2datascanner.projects.admin.adminapp.models.sensitivity_level import Sensitivity
from os2datascanner.projects.admin.adminapp.models.organization_model import Organization


class AnalysisScanTest(django.test.TestCase):

    @staticmethod
    def get_folder_path():
        dir_path = os.path.dirname(os.path.realpath(__file__)) + '/scanner/scanner'
        print('Directory Path:' + dir_path)
        return dir_path


class FileExtractorTest(django.test.TestCase):
    @unittest.expectedFailure
    def test_file_extractor(self):
        with tempfile.TemporaryDirectory(dir=str(data_dir)) as temp_dir:
            filepath1 = temp_dir + '/kk.dk'
            filepath2 = temp_dir + '/æøå'
            os.mkdir(filepath1)
            os.mkdir(filepath2)

            spider = FileSpider(
                FileScanner({"id": create_filescan().pk}),
                None,
            )
            filemap = spider.file_extractor('file://' + temp_dir)

            self.assertTrue(filemap, "What did I expect here?")

            encoded_file_path1 = filemap[0].encode('utf-8')
            encoded_file_path2 = filemap[1].encode('utf-8')

            self.assertEqual(filepath1, encoded_file_path1.decode('utf-8').replace('file://', ''))
            self.assertEqual(filepath2, encoded_file_path2.decode('utf-8').replace('file://', ''))


class ExternalLinkCheckerTest(django.test.TestCase):

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


class NameTest(django.test.TestCase):

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
        name_rule = name.NameRule('The Name Rule', Sensitivity.HIGH,
                                  NameRule.DATABASE_DST_2014)
        matches = name_rule.execute(text)

        self.assertTrue(matches, 'Something went wrong...')

        matches = [re.sub(r'\s+', ' ', m['matched_data']) for m in matches]

        for valid_name in valid_names:
            with self.subTest(valid_name):
                self.assertIn(valid_name, matches,
                              valid_name + " is valid")
        for invalid_name in invalid_names:
            with self.subTest(invalid_name):
                self.assertFalse(any(m == invalid_name for m in matches),
                                 invalid_name + " is valid")


class CPRTest(django.test.TestCase):

    """Test the CPR rule."""

    def check_matches(self, matches, valid_matches, invalid_matches):
        """Check that the matches contains the given valid matches and none
        of the given invalid matches."""
        matched_data = [m['matched_data'] for m in matches]

        for valid_match in valid_matches:
            self.assertIn(valid_match, matched_data)
        for invalid_match in invalid_matches:
            self.assertNotIn(invalid_match, matched_data)

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

        matches = cpr.match_cprs(text, Sensitivity.LOW, mask_digits=False,
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

        matches = cpr.match_cprs(text, Sensitivity.HIGH, mask_digits=False,
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


class PDF2HTMLTest(django.test.TestCase):

    def create_ressources(self, filename):
        src = str(data_dir / 'pdf' / filename)
        dst = str(data_dir / 'tmp' / filename)
        shutil.copy2(src, dst)

        version = Version(
            scan=create_filescan(),
            location=Location(
                url=dst,
                scanner=create_filescanner(),
            ),
        )
        item = ConversionQueueItem(pk=0,
                                   url=version,
                                   file=dst,
                                   type=pdf.PDFProcessor,
                                   status=ConversionQueueItem.NEW)

        with tempfile.TemporaryDirectory(dir=str(data_dir / 'tmp')) as temp_dir:
            result = pdf.PDFProcessor.convert(self, item, temp_dir)

        return result

    def tearDown(self) -> None:
        for p in data_dir.joinpath('tmp').iterdir():
            if p.name != 'README':
                p.unlink()

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


@unittest.skipUnless(os.path.isfile("/usr/lib/libreoffice/program/soffice"),
                     "LibreOffice is unavailable")
class LibreOfficeTest(django.test.TestCase):

    libreoffice_processor = None

    @classmethod
    def setUpClass(self):
        print('Starting libreoffice ressource...')
        self.libreoffice_processor = libreoffice.LibreOfficeProcessor()
        self.libreoffice_processor.setup_queue_processing(1111, 'libreoffice0')

    def tearDown(self) -> None:
        for p in data_dir.joinpath('tmp').iterdir():
            if p.name != 'README':
                p.unlink()

    def create_ressources(self, filename):
        src = str(data_dir / 'libreoffice' / filename)
        dst = str(data_dir / 'tmp' / filename)

        shutil.copy2(src, dst)

        version = Version(
            scan=create_filescan(),
            location=Location(
                url=src,
                scanner=create_filescanner(),
            ),
        )

        item = ConversionQueueItem(url=version,
                                   file=dst,
                                   type=libreoffice.LibreOfficeProcessor,
                                   status=ConversionQueueItem.NEW)

        with tempfile.TemporaryDirectory(dir=str(data_dir / 'tmp')) as temp_dir:
            result = self.libreoffice_processor.convert(item, temp_dir)

        return result

    def test_libreoffice_conversion_success(self):
        filename = 'KK SGP eksempel 2013.02.27.xls'
        if filename is None:
            self.fail("File deos not exists.")
            return
        result = self.create_ressources(filename)
        self.assertEqual(result, True)

    def test_libreoffice_teardown(self):
        self.libreoffice_processor.teardown_queue_processing()
        self.assertEqual(self.libreoffice_processor.unoconv, None)
        self.assertEqual(self.libreoffice_processor.instance, None)


class HTMLTest(django.test.TestCase):

    def create_ressources(self, filename):
        src = str(data_dir / 'html' / filename)
        dst = str(data_dir / 'tmp' / filename)

        shutil.copy2(src, dst)

        version = Version(
            scan=create_filescan(),
            location=Location(
                url=src,
                scanner=create_filescanner(),
            ),
        )
        item = ConversionQueueItem(url=version, file=dst,
                                   type=html.HTMLProcessor,
                                   status=ConversionQueueItem.NEW)

        return item

    def tearDown(self) -> None:
        for p in data_dir.joinpath('tmp').iterdir():
            if p.name != 'README':
                p.unlink()

    def test_html_process_method(self):
        filename = 'Midler-til-frivilligt-arbejde.html'
        item = self.create_ressources(filename)
        self.assertIsNotNone(item, "File does not exist")
        html_processor = html.HTMLProcessor()
        result = html_processor.handle_queue_item(item)
        self.assertEqual(result, True)


class ZIPTest(django.test.TestCase):

    def create_ressources(self, filename):
        src = str(data_dir / 'zip' / filename)
        dst = str(data_dir / 'tmp' / filename)
        shutil.copy2(src, dst)

        version = Version(
            scan=create_filescan(),
            location=Location(
                url=dst,
                scanner=create_filescanner(),
            ),
        )
        item = ConversionQueueItem(pk=0,
                                   url=version,
                                   file=dst,
                                   type=zip.ZipProcessor,
                                   status=ConversionQueueItem.NEW)

        with tempfile.TemporaryDirectory(dir=str(data_dir / 'tmp')) as temp_dir:
            zip_processor = zip.ZipProcessor()
            result = zip_processor.convert(item, temp_dir)

        return result

    def tearDown(self) -> None:
        for p in data_dir.joinpath('tmp').iterdir():
            if p.name != 'README':
                p.unlink()

    def test_unzip_on_password_zip(self):
        filename = 'Nye_Ejere_6.zip'
        result = self.create_ressources(filename)
        self.assertIsNotNone(result, "File does not exist")
        self.assertEqual(result, False)

    def test_unzip(self):
        filename = "contains.zip"
        result = self.create_ressources(filename)
        self.assertIsNotNone(result, "File does not exist")
        self.assertEqual(result, True)


@unittest.skip("ScannerApp no longer exists")
class StoreStatsTest(django.test.TestCase):

    def test_store_stats(self):
        scan_id, scannerapp, webscan = self.create_ressources()

        files_skipped_count = 110
        files_scraped_count = 5
        scannerapp.scanner = Scanner(scan_id)
        scannerapp.scanner_spider = scannerapp.setup_scanner_spider()
        scannerapp.scanner_spider.crawler.stats.set_value('last_modified_check/pages_skipped', files_skipped_count)
        scannerapp.scanner_spider.crawler.stats.set_value('downloader/request_count', files_scraped_count)
        scannerapp.scanner_spider.crawler.stats.get_stats()
        scannerapp.store_stats()
        from os2webscanner.models.statistic_model import Statistic
        statistic = Statistic.objects.get(scan=webscan)
        self.assertEqual(statistic.files_skipped_count, files_skipped_count)
        self.assertEqual(statistic.files_scraped_count, files_scraped_count)

    def create_ressources(self):
        webscan = create_webscan()
        # python 3.4+ should use builtin unittest.mock not mock package
        from unittest.mock import patch

        scan_id = webscan.pk
        args = ['does not matter', scan_id]
        with patch.object(sys, 'argv', args):
            from os2datascanner.engine.run import get_project_settings
            scannerapp = ScannerApp(scan_id, type(webscan).__name__)
            settings = get_project_settings()
            from scrapy.crawler import CrawlerProcess
            scannerapp.crawler_process = CrawlerProcess(settings)
        return scan_id, scannerapp, webscan

    def tearDown(self) -> None:
        for p in data_dir.joinpath('tmp').iterdir():
            if p.name != 'README':
                p.unlink()

    def test_store_multiple_stats(self):
        scan_id, scannerapp, webscan = self.create_ressources()

        for i in range(2):
            files_skipped_count = 110
            files_scraped_count = 5
            scannerapp.scanner = Scanner(scan_id)
            scannerapp.scanner_spider = scannerapp.setup_scanner_spider()
            scannerapp.scanner_spider.crawler.stats.set_value('last_modified_check/pages_skipped', files_skipped_count)
            scannerapp.scanner_spider.crawler.stats.set_value('downloader/request_count', files_scraped_count)
            scannerapp.scanner_spider.crawler.stats.get_stats()
            scannerapp.store_stats()

        from os2datascanner.projects.admin.adminapp.models.statistic_model import Statistic
        statistic = Statistic.objects.get(scan=webscan)
        self.assertEqual(statistic.files_skipped_count, files_skipped_count*2)
        self.assertEqual(statistic.files_scraped_count, files_scraped_count*2)


@unittest.skip("process manager has been refactored")
class ProcessManagerTest(django.test.TestCase):

    @classmethod
    def setUpClass(self):
        process_manager.prepare_processors()
        process_manager.start_all_processors()

    @classmethod
    def tearDownClass(self):
        for pdata in process_manager.process_list:
            process_manager.stop_process(pdata)

    def test_processors_are_prepared(self):
        self.assertEqual(len(process_manager.process_list), 16)

    def test_processors_are_started(self):
        self.assertEqual(len(process_manager.process_map), 32)

    def test_processors_restart(self):
        # Enable time sleep if you want to make sure libreoffice
        # sub-processors(soffice, oopsplash) are started,
        # before trying to stop them again.

        # time.sleep(120)
        for pdata in process_manager.process_list:
            process_manager.stop_process(pdata)
        self.assertEqual(len(process_manager.process_map), 16)
        for pdata in process_manager.process_list:
            process_manager.start_process(pdata)
        self.assertEqual(len(process_manager.process_map), 32)
        # time.sleep(120)


def create_webscan():
    return WebScan.objects.create(
        status=Scan.NEW,
        scanner=create_webscanner()
    )


def create_webscanner():
    return WebScanner.objects.get_or_create(
        name='the web scanner',
        organization=create_organization(),
        url='http://example.com/something/test',
    )[0]


def create_filescan():
    scanner = create_filescanner()
    assert scanner.url
    return Scan.objects.create(status=Scan.NEW,scanner=scanner)


def create_filescanner():
    from os2datascanner.projects.admin.adminapp.models.scannerjobs.filescanner_model import FileScanner

    return FileScanner.objects.get_or_create(
        name='the file scanner',
        url=r'\\example.com\test',
        defaults=dict(organization=create_organization()),
        mountpath=str(test_dir),
        alias='T'
    )[0]


def create_organization():
    return Organization.objects.get_or_create(
        name='Magenta',
        contact_email='info@magenta.dk',
        contact_phone='39393939'
    )[0]


class RegexRuleIsAllMatchTest(django.test.TestCase):

    organization = None

    def create_regexrule(self, name, description, sensitivity):
        rule = RegexRule(name=name,
                         organization=create_organization(),
                         description=description,
                         sensitivity=sensitivity)
        return rule

    def create_scanner_regexrule(self, pattern_objects, rule):
        regex_rule = regexrule.RegexRule(
            name=rule.name,
            pattern_strings=pattern_objects,
            sensitivity=rule.sensitivity,
        )
        return regex_rule

    def test_cpr_and_name_rule(self):
        text = """
        2110625629 Bacon ipsum dolor amet turducken 
        kevin brisket ribeye jowl short l
        tail Danni Als alcatra boudin filet mignon shankle 
        """
        rule = self.create_regexrule('cpr_and_name_rule', 'Finds cpr and name',
                                     Sensitivity.LOW)

        regex_pattern = PatternMockObject()
        regex_rule = self.create_scanner_regexrule(regex_pattern, rule)
        matches = regex_rule.execute(text)
        result = regex_rule.is_all_match(matches)
        self.assertEqual(result, True)

    def test_cpr_name_something_rule_match(self):
        text = """
        Something bacon ipsum dolor amet turducken 
        kevin brisket ribeye 2110625629 jowl short l
        tail Danni Als alcatra boudin filet mignon shankle 
        """
        rule = self.create_regexrule('cpr_name_something_rule',
                                     'Finds cpr, name and the word Something.',
                                     Sensitivity.LOW)

        pattern_objects = PatternMockObjects()
        regex_pattern1 = PatternMockObject()
        regex_pattern2 = PatternMockObject()

        regex_pattern2.pattern_string = 'Something'

        pattern_objects.add_pattern_string(regex_pattern1)
        pattern_objects.add_pattern_string(regex_pattern2)

        regex_rule = self.create_scanner_regexrule(pattern_objects, rule)
        matches = regex_rule.execute(text)
        result = regex_rule.is_all_match(matches)
        self.assertEqual(result, True)

    def test_cpr_name_something_rule_no_match(self):
        text = """
        Something bacon ipsum dolor amet turducken 
        kevin brisket ribeye 2110625629 jowl short l
        tail Danni Als alcatra boudin filet mignon shankle 
        """
        rule = self.create_regexrule('cpr_name_something_rule',
                                     'Finds cpr, name and the word something.',
                                     Sensitivity.LOW)

        pattern_objects = PatternMockObjects()
        regex_pattern1 = PatternMockObject()
        regex_pattern2 = PatternMockObject()

        regex_pattern2.pattern_string = 'something'

        pattern_objects.add_pattern_string(regex_pattern1)
        pattern_objects.add_pattern_string(regex_pattern2)

        regex_rule = self.create_scanner_regexrule(pattern_objects, rule)
        matches = regex_rule.execute(text)
        result = regex_rule.is_all_match(matches)
        self.assertEqual(result, False)

    def test_name_something_rule_match(self):
        text = """
        Something bacon ipsum dolor amet turducken 
        kevin brisket ribeye 2110625629 jowl short l
        tail Danni Als alcatra boudin filet mignon shankle 
        """
        rule = self.create_regexrule('name_something_rule',
                                     'Finds name and the word Something.',
                                     Sensitivity.LOW)

        pattern_objects = PatternMockObjects()
        regex_pattern1 = PatternMockObject()
        regex_pattern2 = PatternMockObject()

        regex_pattern2.pattern_string = 'Something'

        pattern_objects.add_pattern_string(regex_pattern1)
        pattern_objects.add_pattern_string(regex_pattern2)

        regex_rule = self.create_scanner_regexrule(pattern_objects, rule)
        matches = regex_rule.execute(text)
        result = regex_rule.is_all_match(matches)
        self.assertEqual(result, True)


class PatternMockObjects(object):
    """
    This is not pretty but it works :)
    The fastest way for me, to go around django queryset method call in scanner/regexrule.py line 38.
    """

    def __init__(self):
        self.pattern_string_objects = []

    def add_pattern_string(self, pattern_string_obj):
        self.pattern_string_objects.append(pattern_string_obj)

    def all(self):
        return self.pattern_string_objects


class PatternMockObject(object):

    pattern_string = '[A-Z]([a-z]+|\.)(?:\s+[A-Z]([a-z]+|\.))' \
                     '*(?:\s+[a-z][a-z\-]+){0,2}\s+[A-Z]([a-z]+|\.)'

    def all(self):
        return[self]
