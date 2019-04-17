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

import json
import re

import structlog
import regex

from .cpr import CPRRule
from .rule import Rule
from ..items import MatchItem

logger = structlog.get_logger()


class RegexRule(Rule):
    """Represents a rule which matches using a regular expression."""

    def __init__(self, name, pattern_strings, sensitivity, cpr_enabled=False, ignore_irrelevant=False,
                 do_modulus11=False, *args, **kwargs):
        """Initialize the rule.
        The sensitivity is used to assign a sensitivity value to matches.
        """
        # Convert QuerySet to list
        super().__init__(*args, **kwargs)
        self.regex_patterns = list(pattern_strings.all())

        self.name = name
        self.sensitivity = sensitivity
        self.cpr_enabled = cpr_enabled
        self.ignore_irrelevant = ignore_irrelevant
        self.do_modulus11 = do_modulus11
        self.regex_str = ''

        if not self._is_cpr_only():
            logger.debug('Regex patterns', patterns=[
                _psuedoRule.pattern_string
                for _psuedoRule in self.regex_patterns
            ])

            self.regex_str = self.compund_rules()
            self.regex = regex.compile(self.regex_str, regex.DOTALL)

        # bind the 'do_modulus11' and 'ignore_irrelevant' variables to the cpr_enabled property so that they're always
        # false if it is false
        if not cpr_enabled:
            self.do_modulus11 = cpr_enabled
            self.ignore_irrelevant = cpr_enabled

    def __str__(self):
        """
        Returns a string object representation of this object
        :return:
        """

        return json.dumps({
            'name': self.name,
            'regex': self.regex_str,
            'cpr_enabled': self._is_cpr_only(),
            'sensitivity': self.sensitivity,
        }, indent=2)

    def compund_rules(self):
        """
        This method compounds all the regex patterns in the rule set into one regex rule that is OR'ed
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
                if not rule_set:
                    compound_rule += ')'
                else:
                    compound_rule += '|'
            print('Returning< '+compound_rule+' >')
            return compound_rule
        if len(rule_set) < 1:
            return None

    def execute(self, text):
        """Execute the rule on the text."""
        matches = set()

        if self._is_cpr_only():
            cpr_rule = CPRRule(self.name, self.do_modulus11, self.ignore_irrelevant, whitelist=None)
            temp_matches = cpr_rule.execute(text)
            matches.update(temp_matches)
        else:
            re_matches = self.regex.finditer(text)
            if self.cpr_enabled:
                cpr_rule = CPRRule(self.name, self.do_modulus11, self.ignore_irrelevant, whitelist=None)
                matches.update(cpr_rule.execute(text))

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

        # If it turns out that we're only doing a cpr scan then scan for the first match and return true
        if self._is_cpr_only():
            for match in matches:
                if re.match(self.cpr_pattern, match['original_matched_data']):
                    return True
        else:
            regex_patterns = set(self.regex_patterns)

            # for rule in self.regex_patterns:
            for pattern in self.regex_patterns:
                for match in matches:
                    if re.match(pattern.pattern_string, match['matched_data']) and regex_patterns:
                        regex_patterns.pop()
                        continue
                    if self.cpr_enabled and not cpr_match and 'original_matched_data' in match:
                        if re.match(self.cpr_pattern, match['original_matched_data']):
                            cpr_match = True

                if not regex_patterns:
                    break
            if not self.cpr_enabled:
                return not regex_patterns
            else:
                return not regex_patterns and cpr_match

    def _is_cpr_only(self):
        """Just a method to decide if we are only doing a CPR scan."""

        return self.cpr_enabled and len(self.regex_patterns) <= 0
