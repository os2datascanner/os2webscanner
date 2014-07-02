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
        self.regex = regex.compile(match_string)
        self.sensitivity = sensitivity

    def execute(self, text):
        """Execute the rule on the text."""
        matches = set()
        re_matches = self.regex.finditer(text)
        for match in re_matches:
            matches.add(MatchItem(matched_data=match.group(0),
                                  sensitivity=self.sensitivity))
        return matches
