import unittest

from os2datascanner.engine2.model.core import SourceManager


class Tracker:
    special_cookie = object()

    def __init__(self):
        self.count = 0

    def _generate_state(self, sm):
        self.count += 1
        try:
            yield self.special_cookie
        finally:
            self.count -= 1


class Dependent:
    def __init__(self, parent):
        self._parent = parent
        self.count = 0

    def _generate_state(self, sm):
        self.count += 1
        try:
            yield sm.open(self._parent)
        finally:
            self.count -= 1


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

    def test_dependencies(self):
        tracker1 = Tracker()
        tracker2 = Tracker()
        dependent = Dependent(tracker1)
        with SourceManager() as sm:
            sm.open(tracker1)
            sm.open(tracker2)
            sm.open(dependent)

            self.assertEqual(
                    dependent.count,
                    1,
                    "SourceManager didn't open the dependent")

            sm.close(tracker1)

            self.assertEqual(
                    dependent.count,
                    0,
                    "SourceManager didn't close the dependent")
            self.assertEqual(
                    tracker1.count,
                    0,
                    "SourceManager didn't close the parent object")
            self.assertEqual(
                    tracker2.count,
                    1,
                    "SourceManager closed an unrelated object")
        self.assertEqual(
                tracker2.count,
                0,
                "SourceManager didn't eventually close the unrelated object")

    def test_width(self):
        tracker1 = Tracker()
        tracker2 = Tracker()
        tracker3 = Tracker()
        with SourceManager(width=2) as sm:
            sm.open(tracker1)
            sm.open(tracker2)

            self.assertEqual(
                    tracker1.count,
                    1)
            self.assertEqual(
                    tracker2.count,
                    1)

            sm.open(tracker3)

            self.assertEqual(
                    tracker1.count,
                    0)
            self.assertEqual(
                    tracker3.count,
                    1)

    def test_nested_lru(self):
        tracker1 = Tracker()
        tracker2 = Tracker()
        tracker3 = Tracker()
        tracker4 = Dependent(tracker1)
        tracker5 = Dependent(tracker1)
        tracker6 = Dependent(tracker1)
        with SourceManager(width=2) as sm:
            sm.open(tracker1)
            sm.open(tracker2)
            # At this point, the SourceManager is full and tracker1 is the
            # least recently used entry, so it should be evicted next

            # Opening a dependency of tracker1 should mark it as most recently
            # used, meaning that tracker2 will be evicted when we try to open
            # something new
            sm.open(tracker4)
            sm.open(tracker3)

            self.assertEqual(
                    tracker2.count,
                    0)
