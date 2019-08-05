import os
import shutil
import tempfile
import time
import unittest
from datetime import timedelta, datetime

from django.conf import settings
from django.test import TestCase, override_settings

from os2datascanner.projects.admin.adminapp.models.scans.scan_model import Scan

from .util import CreateOrganization, CreateWebScan, CreateScan


@override_settings(VAR_DIR=None)
class ScanModelTest(TestCase):
    """Unit-tests for the Create Scan model."""

    def setUp(self):
        super().setUp()

        CreateOrganization.create_organization(self)

        # CreateExchangeDomain.create_exchangedomain(self)

        self.__tempdir = settings.VAR_DIR = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.__tempdir)

        super().tearDown()

    @unittest.skip("Exchange domain is gone!")
    def test_exchange_cleanup_finished_scan(self):
        exchangescan = CreateExchangeScan.create_exchangescan(self)
        self.check_scan_dir(exchangescan)

    def test_web_cleanup_finished_scan(self):
        webscan = CreateWebScan.create_webscan(self)
        self.check_scan_dir(webscan)

    def test_file_cleanup_finished_scan(self):
        filescan = CreateScan.create_filescan(self)
        self.check_scan_dir(filescan)

    def check_scan_dir(self, scan_object):
        self.assertEqual(
            os.path.commonpath([self.__tempdir, scan_object.scan_dir]),
            self.__tempdir,
            "forcing scandir to /tmp failed!"
        )

        os.makedirs(scan_object.scan_dir)
        self.assertTrue(os.path.exists(scan_object.scan_dir))
        time.sleep(2)
        Scan.cleanup_finished_scans(datetime.now() - timedelta(minutes=1))
        self.assertFalse(os.path.exists(scan_object.scan_dir))
