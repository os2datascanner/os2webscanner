import unittest

from os2datascanner.engine2.model.core import Source
from os2datascanner.engine2.model.data import DataSource
from os2datascanner.engine2.model.file import FilesystemSource
from os2datascanner.engine2.model.http import SecureWebSource, WebSource
from os2datascanner.engine2.model.smb import SMBSource
from os2datascanner.engine2.model.smbc import SMBCSource


class URLTests(unittest.TestCase):
    def test_sources(self):
        sources_and_urls = [
            (FilesystemSource("/usr"), "file:///usr"),
            (
                SMBSource("//10.0.0.30/Share$/Documents"),
                "smb://10.0.0.30/Share%24/Documents",
            ),
            (
                SMBSource("//10.0.0.30/Share$/Documents", "FaithfullA"),
                "smb://FaithfullA@10.0.0.30/Share%24/Documents",
            ),
            (
                SMBSource(
                    "//10.0.0.30/Share$/Documents",
                    "FaithfullA",
                    "secretpassword",
                ),
                "smb://FaithfullA:secretpassword@10.0.0.30/Share%24/Documents",
            ),
            (
                SMBSource(
                    "//10.0.0.30/Share$/Documents",
                    "FaithfullA",
                    "secretpassword",
                    "SYSGRP",
                ),
                "smb://SYSGRP;FaithfullA:secretpassword@10.0.0.30/Share%24"
                "/Documents",
            ),
            (
                SMBSource(
                    "//10.0.0.30/Share$/Documents",
                    "FaithfullA",
                    None,
                    "SYSGRP",
                ),
                "smb://SYSGRP;FaithfullA@10.0.0.30/Share%24/Documents",
            ),
            (
                SMBCSource(
                    "//INT-SRV-01/Q$",
                    "FaithfullA",
                    None,
                    "SYSGRP",
                ),
                "smbc://SYSGRP;FaithfullA@INT-SRV-01/Q%24",
            ),
            (WebSource("http://www.example.com"), "http://www.example.com"),
            (
                SecureWebSource("https://www.example.com"),
                "https://www.example.com",
            ),
            (
                DataSource(b"This is a test", "text/plain"),
                "data:text/plain;base64,VGhpcyBpcyBhIHRlc3Q=",
            ),
        ]

        for source, url in sources_and_urls:
            with self.subTest(url):
                generated_url = source.to_url()
                self.assertEqual(url, generated_url)
