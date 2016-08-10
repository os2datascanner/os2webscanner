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

import regex

from rule import Rule
from ..items import MatchItem


class RegexRule(Rule):

    """Represents a rule which matches using a regular expression."""

    def __init__(self, name, match_string, sensitivity):
        """Initialize the rule.

        The sensitivity is used to assign a sensitivity value to matches.
        """
        self.name = name
        self.regex = regex.compile(match_string, regex.DOTALL)
        self.sensitivity = sensitivity

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
