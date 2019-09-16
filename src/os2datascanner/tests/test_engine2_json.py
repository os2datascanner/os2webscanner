import unittest

from os2datascanner.engine2.model.core import Source
from os2datascanner.engine2.model.data import DataSource, DataHandle
from os2datascanner.engine2.model.file import (
        FilesystemSource, FilesystemHandle)
from os2datascanner.engine2.model.filtered import (
        FilteredSource, FilteredHandle, FilterType)
from os2datascanner.engine2.model.smb import SMBSource, SMBHandle
from os2datascanner.engine2.model.smbc import SMBCSource, SMBCHandle
from os2datascanner.engine2.model.zip import ZipSource, ZipHandle


class JSONTests(unittest.TestCase):
    def test_json_round_trip(self):
        example_handles = [
            FilesystemHandle(
                    FilesystemSource("/usr/share/common-licenses"),
                    "GPL-3"),
            DataHandle(
                    DataSource(b"Test", "text/plain"),
                    "file"),
            FilteredHandle(
                    FilteredSource(
                            FilesystemHandle(
                                    FilesystemSource("/usr/share/doc/coreutils"),
                                    "changelog.Debian.gz"),
                            FilterType.GZIP),
                    "changelog.Debian"),
            SMBHandle(
                    SMBSource(
                            "//SERVER/Resource", "username"),
                    "~ocument.docx"),
            SMBCHandle(
                    SMBCSource(
                            "//SERVER/Resource",
                            "username", "topsecret", "WORKGROUP8"),
                    "~ocument.docx"),
            ZipHandle(
                    ZipSource(
                            SMBCHandle(
                                    SMBCSource(
                                            "//SERVER/Resource",
                                            "username"),
                                    "Confidential Documents.zip")),
                    "doc/Personal Information.docx")
        ]

        for handle in example_handles:
            with self.subTest(handle):
                json = handle.to_json_object()
                print(handle)
                print(json)
                self.assertEqual(handle, handle.from_json_object(json))
                print("--")

