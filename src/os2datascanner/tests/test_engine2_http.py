from datetime import datetime
import unittest
import contextlib

from os2datascanner.engine2.model.core import (
        Source, SourceManager, UnknownSchemeError, ResourceUnavailableError)
from os2datascanner.engine2.model.http import WebSource, WebHandle
from os2datascanner.engine2.rules.types import InputType
from os2datascanner.engine2.conversions.utilities.results import SingleResult


magenta = WebSource("https://www.magenta.dk")


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

    def test_resource(self):
        with SourceManager() as sm:
            first_thing = None
            with contextlib.closing(magenta.handles(sm)) as handles:
                first_thing = next(handles)
            r = first_thing.follow(sm)
            self.assertIsInstance(
                    r.get_last_modified(),
                    SingleResult,
                    ("{0}: last modification date is not a"
                            " SingleResult").format(first_thing))
            self.assertIsInstance(
                    r.get_last_modified().value,
                    datetime,
                    ("{0}: last modification date value is not a"
                            " datetime.datetime").format(first_thing))
            with r.make_stream() as fp:
                stream_raw = fp.read()
            with r.make_path() as p:
                with open(p, "rb") as fp:
                    file_raw = fp.read()
            self.assertEqual(stream_raw, file_raw,
                    "{0}: file and stream not equal".format(first_thing))

    def test_referrer_urls(self):
        with SourceManager() as sm:
            second_thing = None
            with contextlib.closing(magenta.handles(sm)) as handles:
                # We know nothing about the first page (maybe it has a link to
                # itself, maybe it doesn't), but the second page is necessarily
                # something we got to by following a link
                next(handles)
                second_thing = next(handles)
            self.assertTrue(
                    second_thing.get_referrer_urls(),
                    "{0}: followed link doesn't have a referrer".format(
                            second_thing))

    def test_error(self):
        no_such_file = WebHandle(magenta, "/404.404")
        with SourceManager() as sm:
            r = no_such_file.follow(sm)
            self.assertEqual(
                    r.get_status(),
                    404,
                    "{0}: broken link doesn't have status 404".format(
                            no_such_file))
            with self.assertRaises(ResourceUnavailableError):
                r.get_size()
            with self.assertRaises(ResourceUnavailableError):
                with r.make_path() as p:
                    pass
            with self.assertRaises(ResourceUnavailableError):
                with r.make_stream() as s:
                    pass

    def test_missing_headers(self):
        with SourceManager() as sm:
            first_thing = None
            with contextlib.closing(magenta.handles(sm)) as handles:
                first_thing = next(handles)
            r = first_thing.follow(sm)

            now = datetime.now()

            # It is not documented anywhere that WebResource.get_header()
            # returns a live dictionary, so don't depend on this behaviour
            del r.unpack_header()['content-type']
            del r.unpack_header()[InputType.LastModified]

            self.assertEqual(
                    r.compute_type(),
                    "application/octet-stream",
                    "{0}: unexpected backup MIME type".format(first_thing))
            self.assertGreaterEqual(
                    r.get_last_modified().value,
                    now,
                    "{0}: Last-Modified not fresh".format(first_thing))
