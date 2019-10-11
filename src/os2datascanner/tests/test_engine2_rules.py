import unittest

from os2datascanner.engine2.rules.cpr import CPRRule
from os2datascanner.engine2.rules.regex import RegexRule


class RuleTests(unittest.TestCase):
    def test_rule_matches(self):
        candidates = [
            (
                CPRRule(ignore_irrelevant=False),
                """
2205995008: forbryder,
230500 0003: forbryder,
240501-0006: forbryder""",
                [
                    "2205XXXXXX",
                    "2305XXXXXX",
                    "2405XXXXXX"             
                ]
            ),
            (
                CPRRule(ignore_irrelevant=True),
                """
2205995008: forbryder,
230500 0003: forbryder,
240501-0006: forbryder""",
                [
                    "2305XXXXXX",
                    "2405XXXXXX"             
                ]
            ),
            (
                RegexRule("((four|six)( [aopt]+)?|(one|seven) [aopt]+)"),
                """
one
one potato
two potato
three potato
four
five potato
six potato
seven potato
more!""",
                [
                    "one potato",
                    "four",
                    "six potato",
                    "seven potato"
                ]
            )
        ]

        for rule, input_string, expected in candidates:
            with self.subTest(rule):
                matches = rule.match(input_string)
                self.assertEqual(
                        [match["match"] for match in matches], expected)
