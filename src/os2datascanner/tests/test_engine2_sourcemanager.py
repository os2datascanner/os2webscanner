import unittest

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
    def test_basic(self):
        tracker = Tracker()
        with SourceManager() as sm:
            sm.open(tracker)
            sm.open(tracker)
            self.assertEqual(
                    tracker.count,
                    1,
                    "SourceManager opened the same object twice")
        self.assertEqual(
                tracker.count,
                0,
                "SourceManager didn't close the object")
