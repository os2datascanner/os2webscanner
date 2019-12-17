import unittest

from os2datascanner.engine2.model.ews import (
        EWSMailHandle, EWSAccountSource, OFFICE_365_ENDPOINT as CLOUD)
from os2datascanner.engine2.model.smb import SMBSource, SMBHandle
from os2datascanner.engine2.model.smbc import SMBCSource, SMBCHandle
from os2datascanner.engine2.model.derived.zip import ZipSource, ZipHandle


class CensorTests(unittest.TestCase):
    def test_smb_censoring(self):
        example_handles = [
            SMBHandle(
                    SMBSource(
                            "//SERVER/Resource", "username"),
                    "~ocument.docx"),
            SMBCHandle(
                    SMBCSource(
                            "//SERVER/Resource",
                            "username", "topsecret", "WORKGROUP8"),
                    "~ocument.docx"),
        ]

        for handle in example_handles:
            with self.subTest(handle):
                handle = handle.censor()

                self.assertIsNone(handle.source._domain)
                self.assertIsNone(handle.source._password)
                self.assertIsNone(handle.source._user)

    def test_nested_censoring(self):
        handle = ZipHandle(
                ZipSource(
                        SMBCHandle(
                                SMBCSource(
                                        "//SERVER/Resource",
                                        "username", driveletter="W"),
                                "Confidential Documents.zip")),
                "doc/Personal Information.docx")

        self.assertIsNotNone(handle.source.handle.source._user)

        handle = handle.censor()

        self.assertIsNone(handle.source.handle.source._user)
