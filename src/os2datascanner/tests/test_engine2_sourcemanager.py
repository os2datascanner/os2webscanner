import unittest
import contextlib
from os import stat

from os2datascanner.engine2.model.core import (ShareableCookie, SourceManager)
from os2datascanner.engine2.model.http import WebSource, WebHandle


class Tracker:
    special_cookie = object()

    def __init__(self):
        self.count = 0

    def _generate_state(self, sm):
        self.count += 1
        yield self.special_cookie
        self.count -= 1


class ShareableTracker(Tracker):
    special_cookie = ShareableCookie(object())


class Engine2SourceManagerTest(unittest.TestCase):
    def test_opening(self):
        tracker = Tracker()
        with SourceManager() as sm:
            sm.open(tracker)
            sm.open(tracker)
            self.assertEqual(
                    tracker.count,
                    1,
                    "SourceManager opened the same object twice")

    def test_sharing(self):
        tracker1 = Tracker()
        tracker2 = ShareableTracker()

        with SourceManager() as sm:
            cookie1 = sm.open(tracker1)
            cookie2 = sm.open(tracker2)

            shared = sm.share()
            self.assertNotEqual(
                    cookie1,
                    shared.open(tracker1, try_open=False),
                    "shared SourceManager contained non-shareable cookie")
            self.assertEqual(
                    cookie2,
                    shared.open(tracker2, try_open=False),
                    "shared SourceManager did not contain shareable cookie")

    def test_read_only(self):
        with self.assertRaises(TypeError):
            with SourceManager().share() as sm:
                sm.open(tracker)
