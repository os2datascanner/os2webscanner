import unittest
import contextlib
from os import stat

from os2datascanner.engine2.model.utilities import _TypPropEq


class Plain:
    def __init__(self):
        self._prop = 1


class Equal1(_TypPropEq):
    def __init__(self):
        self._prop = 2


class Equal1a(_TypPropEq):
    def __init__(self, other):
        self._prop = 2
        self._other = other


class Equal2(_TypPropEq):
    eq_properties = ('_prop', )

    def __init__(self, other):
        self._prop = 3
        self._other = other


class Equal3(_TypPropEq):
    def __init__(self, other):
        self._prop = 4
        self._other = other

    def __getstate__(self):
        return {"_prop": self._prop}


class Engine2EqualityTest(unittest.TestCase):
    def test(self):
        self.assertNotEqual(
                Plain(),
                Plain(),
                "object equality is weirdly defined")
        self.assertEqual(
                Equal1(),
                Equal1(),
                "_TypPropEq(__dict__) is broken")
        self.assertNotEqual(
                Equal1a(2),
                Equal1a(3),
                "_TypPropEq(__dict__) claims that 2 == 3")
        self.assertEqual(
                Equal2(4),
                Equal2(5),
                "_TypPropEq(eq_properties) is broken")
        self.assertEqual(
                Equal3(4),
                Equal3(5),
                "_TypPropEq(__getstate__) is broken")
