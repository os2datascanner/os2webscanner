# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
"""A set of regular expression-based rules."""
import re

import regex
from ..items import MatchItem


class RuleSet():
    """
    This class encapsulates a collection/set of rules that need to be run
    against an object (i.e. file or web(app) page/site
    """

    def __init__(self, name, rules, sensitivity):
        # in case for some reason we only get a single object that is a single rule
        if not isinstance(rules, list):
            rules = [rules]

        self.rules_list = rules
        # self.rule_set = set(rules)
        self.sensitivity = sensitivity
        self.name = name
        self.regex = regex.compile(self.compund_rules(), regex.DOTALL)

    def compund_rules(self):
        """
        What this method does is it compounds al the rules in the rule set into one regex rule that is OR'ed
        e.g. A ruleSet of {rule1, rule2, rule3} becomes (rule1 | rule2 | rule3)
        :return: RegexRule representing the compound rule
        """

        rule_set = set(self.rules_list)
        if len(rule_set) == 1:
            return rule_set.pop().match_string
        if len(rule_set) > 1:
            compound_rule = '('
            for _ in rule_set:
                compound_rule += rule_set.pop().match_string
                if len(rule_set) <= 0:
                    compound_rule += ')'
                else:
                    compound_rule += '|'
            return compound_rule

    def execute(self, text):
        """
        Executes the compounded rule on the text.
        :param text: the text to search
        :return: a set of matches for the rule
        """
        matches = set()
        re_matches = self.regex.finditer(text)
        for match in re_matches:
            matched_data = match.group(0)
            if len(matched_data) > 1024:
                # TODO: Get rid of magic number
                matched_data = match.group(1)
            matches.add(MatchItem(matched_data=matched_data,
                                  sensitivity=self.sensitivity))
        return matches

    def isAllMatch(self, matches):
        """
        Checks if each rule is matched with the provided list of matches
        :param matches: List of matches
        :return: {True | false}
        """
        if not isinstance(matches, set):
            return False

        rule_set = set(self.rules_list)
        for rule in rule_set:
            for match in matches:
                if re.match(rule.match_string, match.matched_data):
                    rule_set.pop()
                    continue

        if not rule_set:
            return True
        else:
            return False



