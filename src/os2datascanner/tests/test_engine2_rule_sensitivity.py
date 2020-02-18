from datetime import datetime, timezone
import unittest

from os2datascanner.engine2.rules.rule import Rule, Sensitivity

from os2datascanner.engine2.rules.cpr import CPRRule
from os2datascanner.engine2.rules.dummy import FallbackRule
from os2datascanner.engine2.rules.regex import RegexRule
from os2datascanner.engine2.rules.logical import OrRule, AndRule


def run_rule(rule, in_v):
    results = {}
    while isinstance(rule, Rule):
        imm, pve, nve = rule.split()

        if imm in results:
            matches = imm[results]
        else:
            matches = list(imm.match(in_v))
            results[imm] = matches

        if matches:
            rule = pve
        else:
            rule = nve
    return (rule, results)


class RuleSensitivityTests(unittest.TestCase):
    def test_sensitivity_matches(self):
        rule = AndRule(
                RegexRule("bad thing"),
                OrRule(
                        RegexRule("very bad", sensitivity=Sensitivity.CRITICAL),
                        RegexRule("moderately bad", sensitivity=Sensitivity.PROBLEM),
                        RegexRule("slightly bad", sensitivity=Sensitivity.WARNING),
                        FallbackRule(sensitivity=Sensitivity.INFORMATION)
                    ))

        expected = [
                ("very bad thing", Sensitivity.CRITICAL),
                ("moderately bad thing", Sensitivity.PROBLEM),
                ("moderately bad very bad thing", Sensitivity.CRITICAL),
                ("slightly moderately bad thing", Sensitivity.PROBLEM),
                ("moderately slightly bad thing", Sensitivity.WARNING),
                ("bad thing", Sensitivity.INFORMATION),
                ("moderately quite bad thing", Sensitivity.INFORMATION)
        ]

        for in_v, sensitivity in expected:
            matched, results = run_rule(rule, in_v)
            self.assertEqual(matched, True)
            self.assertEqual(sensitivity, max(
                    [rule.sensitivity for rule, matches in results.items()
                            if rule.sensitivity is not None and matches],
                    key=lambda sensitivity: sensitivity.value))
