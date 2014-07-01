import regex
from datetime import datetime

from rule import Rule
from os2webscanner.models import Sensitivity
from ..items import MatchItem


class CPRRule(Rule):
    name = 'cpr'

    def execute(self, text):
        matches = match_cprs(text)
        return matches

# TODO: Improve
cpr_regex = regex.compile("\\b(\\d{6})[\\s\-]?(\\d{4})\\b")


def date_check(cpr):
    """Check a CPR number for a valid date.
    The CPR number is passed as a string of sequential digits with no spaces
    or dashes."""
    day = int(cpr[0:2])
    month = int(cpr[2:4])
    year = int(cpr[4:6])

    year_check = int(cpr[7])

    # Convert 2-digit year to 4-digit:
    if year_check >= 0 and year_check <= 3:
        year += 1900
    elif year_check == 4:
        if year > 36:
            year += 1900
        else:
            year += 2000
    elif year_check >= 5 and year_check <= 8:
        if year > 57:
            year += 1800
        else:
            year += 2000
    elif year_check == 9:
        if year > 37:
            year += 1900
        else:
            year += 2000

    try:
        datetime(day=day, month=month, year=year)
        return True
    except ValueError:
        # Invalid date
        return False


def match_cprs(text, mask_digits=True):
    it = cpr_regex.finditer(text)
    matches = set()
    for m in it:
        cpr = m.group(1) + m.group(2)
        valid_date = date_check(cpr)
        if mask_digits:
            # Mask last 6 digits
            cpr = cpr[0:4] + "XXXXXX"
        if valid_date:
            matches.add(
                MatchItem(matched_data=cpr, sensitivity=Sensitivity.HIGH))
    return matches
