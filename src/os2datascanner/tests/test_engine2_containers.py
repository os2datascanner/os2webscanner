#!/usr/bin/env python
import unittest

from os2datascanner.engine2.model.core import Source, SourceManager
from os2datascanner.engine2.model.data import DataSource
import os.path

here_path = os.path.dirname(__file__)
test_data_path = os.path.join(here_path, "data", "engine2")


class Engine2ContainerTest(unittest.TestCase):
    def setUp(self) -> None:
        with open(os.path.join(test_data_path, "test-vector"), "rt") as fp:
            self.correct_content = fp.read()

    def test(self):
        with SourceManager() as sm:

            def process(source, depth=0):
                for handle in source.handles(sm):
                    print("{0}{1}".format("  " * depth, handle))
                    derived_source = Source.from_handle(handle)
                    if derived_source:
                        process(derived_source, depth + 1)
                    elif handle.get_name() == "url":
                        with handle.follow(sm).make_stream() as fp:
                            url = fp.read().decode("utf-8")
                        process(Source.from_url(url), depth + 1)
                    elif handle.get_name() == "test-vector" or isinstance(
                        source, DataSource
                    ):
                        with handle.follow(sm).make_stream() as fp:
                            content = fp.read().decode("utf-8")
                        self.assertEqual(
                            content,
                            self.correct_content,
                            "{0}{1} OK".format("  " * depth, handle),
                        )

            process(Source.from_url("file://" + test_data_path))
