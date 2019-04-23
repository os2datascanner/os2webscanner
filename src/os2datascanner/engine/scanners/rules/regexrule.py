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

from .rule import Rule
from ..items import MatchItem

logger = structlog.get_logger()


class RegexRule(Rule):
    """Represents a rule which matches using a regular expression."""

    def __init__(self, name, pattern_strings, sensitivity, *args, **kwargs):
        """Initialize the rule.
        The sensitivity is used to assign a sensitivity value to matches.
        """
        # Convert QuerySet to list
        super().__init__(*args, **kwargs)
        self.regex_patterns = list(pattern_strings.all())

        self.name = name
        self.sensitivity = sensitivity
        self.regex_str = ''

        logger.debug('Regex patterns', patterns=[
            _psuedoRule.pattern_string
            for _psuedoRule in self.regex_patterns
        ])

        self.regex_str = self.compund_rules()
        self.regex = regex.compile(self.regex_str, regex.DOTALL)

    def __str__(self):
        """
        Returns a string object representation of this object
        :return:
        """

        return json.dumps({
            'name': self.name,
            'regex': self.regex_str,
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
                if re.match(pattern.pattern_string, match['matched_data']) and regex_patterns:
                    regex_patterns.pop()
                    continue

            if not regex_patterns:
                break
        return not regex_patterns
