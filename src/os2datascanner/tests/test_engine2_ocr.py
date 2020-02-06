import  os.path
import  unittest

from    os2datascanner.engine2.model.core import SourceManager
from    os2datascanner.engine2.model.file import FilesystemSource
from    os2datascanner.engine2.rules.types import InputType
from    os2datascanner.engine2.conversions import convert

here_path = os.path.dirname(__file__)
test_data_path = os.path.join(here_path, "data", "ocr")
expected_result = "131016-9996"


class TestEngine2OCR(unittest.TestCase):
    def test_ocr_conversions(self):
        fs = FilesystemSource(test_data_path)
        with SourceManager() as sm:
            for h in fs.handles(sm):
                self.assertEqual(
                        convert(h.follow(sm), InputType.Text).value,
                        expected_result,
                        "{0} failed".format(h))
