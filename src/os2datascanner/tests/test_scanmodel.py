import os
import time
import unittest
from datetime import timedelta

from django.test import TestCase

from os2datascanner.projects.admin.adminapp.models.scans.scan_model import Scan

from .util import CreateOrganization, CreateWebScan, CreateScan


class ScanModelTest(TestCase):
    """Unit-tests for the Create Scan model."""

    def setUp(self):
        CreateOrganization.create_organization(self)
        # CreateExchangeDomain.create_exchangedomain(self)


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
        os.makedirs(scan_object.scan_dir)
        self.assertTrue(os.path.exists(scan_object.scan_dir))
        time.sleep(2)
        Scan.cleanup_finished_scans(timedelta(minutes=1))
        self.assertFalse(os.path.exists(scan_object.scan_dir))
