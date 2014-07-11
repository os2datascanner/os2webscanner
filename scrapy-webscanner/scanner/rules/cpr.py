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
"""Rules for CPR scanning."""

import regex
from datetime import datetime

from rule import Rule
from os2webscanner.models import Sensitivity
from ..items import MatchItem


class CPRRule(Rule):

    """Represents a rule which scans for CPR numbers."""

    name = 'cpr'

    def execute(self, text):
        """Execute the CPR rule."""
        matches = match_cprs(text)
        return matches

# TODO: Improve
cpr_regex = regex.compile("\\b(\\d{6})[\\s\-/\\.]?(\\d{4})\\b")


def date_check(cpr):
    """Check a CPR number for a valid date.

    The CPR number is passed as a string of sequential digits with no spaces
    or dashes.
    """
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
    """Return MatchItem objects for each CPR matched in the given text.

    If mask_digits is False, then the matches will contain full CPR numbers.
    """
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
