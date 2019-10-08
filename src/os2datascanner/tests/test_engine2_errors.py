import unittest
import contextlib

from os2datascanner.engine2.model.core import (
        Source, SourceManager, UnknownSchemeError, ResourceUnavailableError)
from os2datascanner.engine2.model.file import FilesystemSource


class Engine2TestErrors(unittest.TestCase):
    def test_relative_filesystemsource(self):
        with self.assertRaises(ValueError):
            FilesystemSource("data/")

    def test_invalid_scheme(self):
        with self.assertRaises(UnknownSchemeError):
            Source.from_url("xxx-invalid://data/20")

    def test_invalid_url(self):
        with self.assertRaises(UnknownSchemeError):
            Source.from_url("Well, this just isn't a URL at all!")

    def test_double_scheme_registration(self):
        with self.assertRaises(ValueError):
            @Source.url_handler("file")
            class Dummy:
                pass

    def test_double_mime_registration(self):
        with self.assertRaises(ValueError):
            @Source.mime_handler("application/zip")
            class Dummy:
                pass

    def test_handles_failure(self):
        print("thf")
        with self.assertRaises(ResourceUnavailableError):
            try:
                with SourceManager() as sm:
                    source = Source.from_url("http://example.invalid/")
                    with contextlib.closing(source.handles(sm)) as handles:
                        print(next(handles))
            except Exception as ex:
                print(ex)
                raise ex
        print("/thf")
