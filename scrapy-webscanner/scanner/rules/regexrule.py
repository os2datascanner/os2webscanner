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

import logging
import re

import regex

from .cpr import CPRRule
from .rule import Rule
from ..items import MatchItem


class RegexRule(Rule):
    """Represents a rule which matches using a regular expression."""

    def __init__(self, name, pattern_strings, sensitivity, cpr_enabled=False, ignore_irrelevant=False, do_modulus11=False):
        """Initialize the rule.
        The sensitivity is used to assign a sensitivity value to matches.
        """
        # Convert QuerySet to list
        self.regex_patterns = list(pattern_strings.all())
        logging.info('------- Regex patters ---------')
        for _psuedoRule in self.regex_patterns:
            logging.info(_psuedoRule.pattern_string)
        logging.info('-----------------------------\n')

        self.name = name
        self.sensitivity = sensitivity
        self.regex_str = self.compund_rules()
        self.regex = regex.compile(self.regex_str, regex.DOTALL)
        self.cpr_enabled = cpr_enabled
        self.ignore_irrelevant = ignore_irrelevant
        self.do_modulus11 = do_modulus11
        # bind the 'do_modulus11' and 'ignore_irrelevant' variables to the cpr_enabled property so that they're always
        # false if it is false
        if not cpr_enabled:
            self.do_modulus11 = cpr_enabled
            self.ignore_irrelevant = cpr_enabled

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
        What this method does is it compounds all the regex patterns in the rule set into one regex rule that is OR'ed
        e.g. A ruleSet of {pattern1, pattern2, pattern3} becomes (pattern1 | pattern2 | pattern3)
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

        if self.cpr_enabled:
            cpr_rule = CPRRule(self.do_modulus11, self.ignore_irrelevant, whitelist=None)
            matches.add(cpr_rule.execute(text))

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

        cpr_match = False

        regex_patterns = set(self.regex_patterns)

        # for rule in self.regex_patterns:
        for pattern in self.regex_patterns:
            for match in matches:
                print('The matched data vs matched_string ' + pattern.pattern_string + ' :: ' + match['matched_data'])

                if re.match(pattern.pattern_string, match['matched_data']) and regex_patterns:
                    regex_patterns.pop()
                    break
                if self.cpr_enabled:
                    if re.match(self.cpr_pattern, match['matched_data']):
                        cpr_match = True

            if not regex_patterns:
                break

        return not regex_patterns and cpr_match
