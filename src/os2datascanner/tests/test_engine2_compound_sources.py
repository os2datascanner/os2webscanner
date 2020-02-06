import os.path
import unittest

from os2datascanner.engine2.model.core import Source, SourceManager
from os2datascanner.engine2.model.file import FilesystemHandle
from os2datascanner.engine2.model.derived.pdf import PDFSource
from os2datascanner.engine2.model.derived.libreoffice import LibreOfficeSource
from os2datascanner.engine2.rules.cpr import CPRRule
from os2datascanner.engine2.rules.types import InputType
from os2datascanner.engine2.conversions import convert


here_path = os.path.dirname(__file__)
test_data_path = os.path.join(here_path, "data")


def try_apply(sm, source, rule):
    for handle in source.handles(sm):
        derived = Source.from_handle(handle, sm)
        if derived:
            yield from try_apply(sm, derived, rule)
        else:
            resource = handle.follow(sm)
            representation = convert(resource, rule.operates_on)
            if representation:
                yield from rule.match(representation)


class Engine2CompoundSourceTest(unittest.TestCase):
    def setUp(self):
        self.rule = CPRRule(modulus_11=False, ignore_irrelevant=False)

    def run_rule(self, source):
        with SourceManager() as sm:
            results = list(try_apply(sm, source, self.rule))
            self.assertEqual(
                    results,
                    [
                        {
                            "offset": 0,
                            "match": "1310XXXXXX",
                            "context": "XXXXXX-XXXX",
                            "context_offset": 0
                        }
                    ])

    def test_libreoffice_source(self):
        self.run_rule(
                LibreOfficeSource(
                        FilesystemHandle.make_handle(
                                os.path.join(
                                        test_data_path,
                                        "libreoffice/embedded-cpr.odt"))))

    def test_pdf_source(self):
        self.run_rule(
                PDFSource(
                        FilesystemHandle.make_handle(
                                os.path.join(
                                        test_data_path,
                                        "pdf/embedded-cpr.pdf"))))
