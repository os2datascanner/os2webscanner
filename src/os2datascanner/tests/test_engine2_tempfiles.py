import unittest
import os.path

from os2datascanner.engine2.model.utilities import NamedTemporaryResource


test_string = "T e s t\ns t r i n g."


class Engine2TempfilesTest(unittest.TestCase):
    def test(self):
        with NamedTemporaryResource("test.txt") as ntr:
            path = ntr.get_path()
            directory = os.path.basename(path)
            self.assertFalse(
                    os.path.exists(path),
                    "temp file {0} shouldn't exist yet".format(path))
            with ntr.open("wt") as fp:
                fp.write(test_string)
            self.assertTrue(
                    os.path.exists(path),
                    "temp file {0} was not created".format(path))
            with open(path, "rt") as fp:
                content = fp.read()
                self.assertEqual(
                        content,
                        test_string,
                        "temp file content '{0}' is incorrect".format(content))
        self.assertFalse(
                os.path.exists(path),
                "temp file {0} wasn't cleaned up".format(path))
        self.assertFalse(
                os.path.exists(directory),
                "temp directory {0} wasn't cleaned up".format(directory))
