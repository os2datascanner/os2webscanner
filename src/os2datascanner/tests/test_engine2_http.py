import unittest
import contextlib
from os import stat

from os2datascanner.engine2.model.core import (
        Source, SourceManager, UnknownSchemeError, ResourceUnavailableError)
from os2datascanner.engine2.model.http import WebSource, WebHandle


magenta = WebSource("https://www.magenta.dk/")


class Engine2HTTPTest(unittest.TestCase):
    def test_exploration(self):
        count = 0
        with SourceManager() as sm:
            for h in magenta.handles(sm):
                if count == 10:
                    break
                else:
                    count += 1
        self.assertEqual(
                count,
                10,
                "magenta.dk should have more than 10 pages")

    def test_download(self):
        count = 0
        with SourceManager() as sm:
            first_thing = None
            with contextlib.closing(magenta.handles(sm)) as handles:
                first_thing = next(handles)
            r = first_thing.follow(sm)
            with r.make_path() as p:
                pass

    def test_error(self):
        no_such_file = WebHandle(magenta, "/404.404")
        with SourceManager() as sm:
            with self.assertRaises(ResourceUnavailableError):
                no_such_file.follow(sm).get_size()
