import regex

from rule import Rule
from os2webscanner.models import Match

class RegexRule(Rule):
    def __init__(self, name, match_string, sensitivity):
        self.name = name
        self.regex = regex.compile(match_string)
        self.sensitivity = sensitivity

    def execute(self, text):
        matches = set()
        re_matches = self.regex.finditer(text)
        for match in re_matches:
            matches.add(Match(matched_data = match.group(0), sensitivity = self.sensitivity))
        return matches