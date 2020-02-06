import unittest

from os2datascanner.engine2.conversions.utilities.results import (
        SingleResult, MultipleResults)


class MultipleResultsTest(unittest.TestCase):
    def test_operators(self):
        mr = MultipleResults()

        mr["first"] = 1
        mr["second"] = 2
        mr["third"] = 3
        mr["fourth"] = 4

        for k, v in mr.items():
            self.assertIsInstance(
                    v,
                    SingleResult)
            self.assertEqual(
                    v.parent,
                    mr)

        del mr["first"]
        del mr["third"]

        self.assertEqual(
                2,
                len(mr.keys()))

    def expect_sr(self, obj, parent):
        self.assertIsInstance(
                obj,
                SingleResult)
        self.assertEqual(
                obj.parent,
                parent)

    def test_simple_constructor(self):
        mr = MultipleResults(a="alpha", b="beta", g="gamma", d="delta")
        for k, v in mr.items():
            self.expect_sr(v, mr)

    def test_import_constructor(self):
        d = {"one": 1, "two": 2, "three": 3, "four": 4}
        mr = MultipleResults(d)
        for k, v in mr.items():
            self.expect_sr(v, mr)
            self.assertEqual(d[k], v.value)

    def test_mr_constructor(self):
        base = MultipleResults(one=1, two=2, three=3, four=4)
        mr = MultipleResults(base, five=5, six=6, seven=7, eight=8)
        for k, v in mr.items():
            self.expect_sr(v, mr)

    def test_get(self):
        mr = MultipleResults()
        v = mr.get("nonsuch", 100)
        self.expect_sr(v, mr)
        self.assertEqual(v.value, 100)
        self.assertNotIn("nonsuch", mr)

    def test_setdefault(self):
        mr = MultipleResults(found=200)

        v = mr.setdefault("nonsuch", 100)
        self.expect_sr(v, mr)
        self.assertEqual(v.value, 100)
        self.assertEqual(v, mr.get("nonsuch"))

        v = mr.setdefault("found", 400)
        self.expect_sr(v, mr)
        self.assertEqual(v.value, 200)
