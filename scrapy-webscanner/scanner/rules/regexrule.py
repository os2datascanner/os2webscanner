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
"""Regular expression-based rules."""

import re
import regex
import logging

from .rule import Rule
from ..items import MatchItem
from os2webscanner.models.regexpattern_model import RegexPattern


class RegexRule(Rule):
    """Represents a rule which matches using a regular expression."""

    def __init__(self, name, pattern_strings, sensitivity):
        """Initialize the rule.
        The sensitivity is used to assign a sensitivity value to matches.
        """
        # Convert QuerySet to list
        self.regex_patterns = list(pattern_strings.all())
        print('Rules is now list: ' + str(type(self.regex_patterns) is list))
        print('Rules 1 is string: ' + str(type(self.regex_patterns[0]) is RegexPattern))
        for _psuedoRule in self.regex_patterns:
            print('----------------')
            print(_psuedoRule.pattern_string)
            print('-----------\n')

        self.name = name
        self.sensitivity = sensitivity
        self.regex_str = self.compund_rules()
        self.regex = regex.compile(self.regex_str, regex.DOTALL)

    def __str__(self):
        """
        Returns a string object repreesentation of this object
        :return:
        """
        return '{\n\tname: ' + self.name + \
               ',\n\tregex: ' + self.regex_str + \
               ',\n\tsensitivity: ' + str(self.sensitivity) + '\n}'

    def compund_rules(self):
        """
        What this method does is it compounds al the rules in the rule set into one regex rule that is OR'ed
        e.g. A ruleSet of {rule1, rule2, rule3} becomes (rule1 | rule2 | rule3)
        :return: RegexRule representing the compound rule
        """

        rule_set = set(self.regex_patterns)
        if len(rule_set) == 1:
            return rule_set.pop().pattern_string
        if len(rule_set) > 1:
            compound_rule = '('
            for _ in self.regex_patterns:
                compound_rule += rule_set.pop().pattern_string
                if len(rule_set) <= 0:
                    compound_rule += ')'
                else:
                    compound_rule += '|'
            print('Returning< '+compound_rule+' >')
            return compound_rule

    def execute(self, text):
        """Execute the rule on the text."""
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

    def is_all_match(self, matches):
        """
        Checks if each rule is matched with the provided list of matches
        :param matches: List of matches
        :return: {True | false}
        """
        if not isinstance(matches, set):
            return False

        regex_patterns = set(self.regex_patterns)

        # for rule in self.regex_patterns:
        for pattern in self.regex_patterns:
            for match in matches:
                print('The matched data vs matched_string ' + pattern.pattern_string + ' :: ' + match['matched_data'])

                if re.match(pattern.pattern_string, match['matched_data']) and regex_patterns:
                    regex_patterns.pop()
                    break

            if not regex_patterns:
                break

        return not regex_patterns
