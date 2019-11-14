import unittest

from os2datascanner.engine2.utilities.equality import TypePropertyEquality


class Plain:
    def __init__(self):
        self._prop = 1


class Equal1(TypePropertyEquality):
    def __init__(self):
        self._prop = 2


class Equal1a(TypePropertyEquality):
    def __init__(self, other):
        self._prop = 2
        self._other = other


class Equal2(TypePropertyEquality):
    eq_properties = ('_prop', )

    def __init__(self, other):
        self._prop = 3
        self._other = other


class Equal3(TypePropertyEquality):
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
                "TypePropertyEquality(__dict__) is broken")
        self.assertNotEqual(
                Equal1a(2),
                Equal1a(3),
                "TypePropertyEquality(__dict__) claims that 2 == 3")
        self.assertEqual(
                Equal2(4),
                Equal2(5),
                "TypePropertyEquality(eq_properties) is broken")
        self.assertEqual(
                Equal3(4),
                Equal3(5),
                "TypePropertyEquality(__getstate__) is broken")
