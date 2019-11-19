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
from datetime import date

import regex

from os2datascanner.engine2.rules.cpr import (
        cpr_regex, date_check, modulus11_check)

from .rule import Rule
from ..items import MatchItem


def load_whitelist(whitelist):
    """Load a list of names from a multi-line string, one name per line.

    Returns a set of the names in all upper-case characters
    """
    return set(
        [
            line.upper().strip() for line in whitelist.splitlines()
        ] if whitelist else []
    )


class CPRRule(Rule):

    """Represents a rule which scans for CPR numbers."""

    def __init__(self, name, sensitivity,
            do_modulus11, ignore_irrelevant, whitelist=None):
        """Initialize the CPR Rule."""
        super().__init__(name, sensitivity)

        self.ignore_irrelevant = ignore_irrelevant
        self.do_modulus11 = do_modulus11
        self.whitelist = load_whitelist(whitelist)

    def execute(self, text, mask_digits=True):
        """Execute the CPR rule."""
        matches = match_cprs(text,
                             sensitivity=self.sensitivity,
                             do_modulus11=self.do_modulus11,
                             ignore_irrelevant=self.ignore_irrelevant,
                             mask_digits=mask_digits,
                             whitelist=self.whitelist)
        return matches


_cpr_regex = regex.compile(cpr_regex)


def match_cprs(text, sensitivity, do_modulus11=True, ignore_irrelevant=True,
               mask_digits=True, whitelist=[]):
    """Return MatchItem objects for each CPR matched in the given text.

    If mask_digits is False, then the matches will contain full CPR numbers.
    """
    it = _cpr_regex.finditer(text)
    matches = set()
    for m in it:
        cpr = m.group(1).replace(' ', '') + m.group(2)
        if cpr in whitelist:
            continue
        valid_date = date_check(cpr, ignore_irrelevant)
        if do_modulus11:
            try:
                valid_modulus11 = modulus11_check(cpr)
            except ValueError:
                valid_modulus11 = True
        else:
            valid_modulus11 = True
        original_cpr = m.group(0)
        if mask_digits:
            # Mask last 6 digits
            cpr = cpr[0:4] + "XXXXXX"
        # Calculate context.
        low, high = m.span()
        if low < 50:
            # Sanity
            low = 50
        match_context = text[low - 50:high + 50]
        match_context = regex.sub(_cpr_regex, "XXXXXX-XXXX", match_context)

        if valid_date and valid_modulus11:
            matches.add(MatchItem(
                matched_data=cpr,
                sensitivity=sensitivity,
                match_context=match_context,
                original_matched_data=original_cpr,
            ))
    return matches
