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


cpr_regex = regex.compile(
    r"\b(\d{2}[\s]?\d{2}[\s]?\d{2})(?:[\s\-/\.]|\s\-\s)?(\d{4})\b"
)

#
# Updated list of dates with CPR numbers violating the Modulo-11 check,
# as of July 2019.
# Source: https://cpr.dk/cpr-systemet/personnumre-uden-kontrolciffer-modulus-11-kontrol/
#
cpr_exception_dates = {
    date(1960, 1, 1),
    date(1964, 1, 1),
    date(1965, 1, 1),
    date(1966, 1, 1),
    date(1969, 1, 1),
    date(1970, 1, 1),
    date(1980, 1, 1),
    date(1982, 1, 1),
    date(1984, 1, 1),
    date(1985, 1, 1),
    date(1986, 1, 1),
    date(1987, 1, 1),
    date(1987, 12, 1),
    date(1988, 1, 1),
    date(1989, 1, 1),
    date(1990, 1, 1),
    date(1991, 1, 1),
    date(1992, 1, 1),
}


THIS_YEAR = date.today().year


def date_check(cpr, ignore_irrelevant=True):
    """Check a CPR number for a valid date.

    The CPR number is passed as a string of sequential digits with no spaces
    or dashes.
    If ignore_irrelevant is True, then CPRs with a
    7th digit of 5, 6, 7, or 8 AND year > 37 will be considered invalid.
    """
    try:
        _get_birth_date(cpr, ignore_irrelevant=ignore_irrelevant)
        return True
    except ValueError:
        # Invalid date
        return False


def _get_birth_date(cpr, ignore_irrelevant=True):
    """Get the birth date as a datetime from the CPR number.

    If the CPR has an invalid birthday, raises ValueError.

    If ignore_irrelevant is True, then CPRs with a
    7th digit of 5, 6, 7, or 8 AND year > 37 will be considered invalid.
    """
    day = int(cpr[0:2])
    month = int(cpr[2:4])
    year = int(cpr[4:6])

    year_check = int(cpr[6])

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

    if ignore_irrelevant:
        if year > THIS_YEAR + 2 or year < 1900:
            raise ValueError(cpr)

    return date(day=day, month=month, year=year)


def _is_modulus11(cpr):
    """Perform a modulus-11 check on the CPR number.

    This should not be called directly as it does not make any exceptions
    for numbers for which the modulus-11 check should not be performed.
    """
    checksum = int(cpr[0]) * 4 + \
        int(cpr[1]) * 3 + \
        int(cpr[2]) * 2 + \
        int(cpr[3]) * 7 + \
        int(cpr[4]) * 6 + \
        int(cpr[5]) * 5 + \
        int(cpr[6]) * 4 + \
        int(cpr[7]) * 3 + \
        int(cpr[8]) * 2 + \
        int(cpr[9]) * 1
    return checksum % 11 == 0


def modulus11_check(cpr):
    """Perform a modulo-11 check on a CPR number with exceptions.

    Return True if the number either passes the modulus-11 check OR is one
    assigned to a person born on one of the exception dates where the
    modulus-11 check should not be applied.
    """
    try:
        birth_date = _get_birth_date(cpr, ignore_irrelevant=False)
    except ValueError:
        return False

    # Return True if the birth dates are one of the exceptions to the
    # modulus 11 rule.
    if birth_date in cpr_exception_dates:
        return True
    else:
        # Otherwise, perform the modulus-11 check
        return _is_modulus11(cpr)


def match_cprs(text, sensitivity, do_modulus11=True, ignore_irrelevant=True,
               mask_digits=True, whitelist=[]):
    """Return MatchItem objects for each CPR matched in the given text.

    If mask_digits is False, then the matches will contain full CPR numbers.
    """
    it = cpr_regex.finditer(text)
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
        match_context = regex.sub(cpr_regex, "XXXXXX-XXXX", match_context)

        if valid_date and valid_modulus11:
            matches.add(MatchItem(
                matched_data=cpr,
                sensitivity=sensitivity,
                match_context=match_context,
                original_matched_data=original_cpr,
            ))
    return matches
