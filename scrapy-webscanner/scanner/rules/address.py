# coding=utf-8
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

"""Rules for name scanning."""

import regex
import os
import codecs

from rule import Rule
from os2webscanner.models import Sensitivity
from ..items import MatchItem

# Match whitespace except newlines
_whitespace = "[^\\S\\n\\r]+"
_simple_name = "\\p{Uppercase}(\\p{L}+|\\.?)"
_house_number = "[1-9][0-9]*[a-zA-Z]?"
_zip_code = "[1-9][0-9][0-9][0-9]"

_street_address = "(?P<street_name>{0})(?P<house_number>{1}{2})?".format(
    _simple_name, _whitespace, _house_number
)
_zip_city = "(?P<zip_code>{0}){1}(?P<city>{2})".format(
    _zip_code,
    _whitespace,
    _simple_name
)
_optional_comma = ",?"
_optional_whitespace = "[^\\S\\n\\r]?"

full_address_regex = regex.compile(
    "\\b" + _street_address + _optional_comma + "(" + _optional_whitespace +
    _zip_city + ")?" + "\\b",
    regex.UNICODE
)


def match_full_address(text):
    """Return possible address matches in the given text."""
    matches = set()
    it = full_address_regex.finditer(text, overlapped=False)
    for m in it:
        street_address = m.group("street_name")
        house_number = m.group("house_number")
        try:
            zip_code = m.group("zip_code")
        except IndexError:
            zip_code = ''
        try:
            city = m.group("city")
        except IndexError:
            city = ''

        if not house_number is None:
            house_number = house_number.lstrip()
        else:
            house_number = ''
        matched_text = m.group(0)
        matches.add(
            (street_address, house_number, zip_code, city, matched_text)
        )
    return matches


def load_name_file(file_name):
    r"""Load a data file containing persons names in uppercase.

    The names should be separated by a tab character followed by a number,
    one name per line.

    The file is of the format:
    NAME\t12312

    Return a list of all the names in unicode.
    :param file_name:
    :return:
    """
    names = []
    for line in codecs.open(file_name, "r", "latin-1"):
        names.append(unicode(line.strip().upper()))
    return names


def load_whitelist(whitelist):
    """Load a list of names from a multi-line string, one name per line.

    Returns a set of the names in all upper-case characters
    """
    if whitelist:
        return set([line.upper().strip() for line in whitelist.splitlines()])
    else:
        return set()


class AddressRule(Rule):

    """Represents a rule which scans for Full Names in text.

    The rule loads a list of names from first and last name files and matches
    names against them to determine the sensitivity level of the matches.
    Matches against full, capitalized, names with up to 2 middle names.
    """

    name = 'address'
    _data_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__)))) + '/data'
    _street_name_file = 'gadenavne.txt'

    def __init__(self, whitelist=None, blacklist=None):
        """Initialize the rule with an optional whitelist.

        The whitelist should contains a multi-line string, with one name per
        line.
        """
        # Load first and last names from data files
        self.street_names = load_name_file(
            self._data_dir + '/' + self._street_name_file
        )
        # Convert to sets for efficient lookup
        self.street_names = set(self.street_names)
        self.whitelist = load_whitelist(whitelist)
        self.blacklist = load_whitelist(blacklist)

    def execute(self, text):
        """Execute the Name rule."""
        matches = set()
        unmatched_text = text

        # Check for whole addresses, i.e. at least street name + house
        # number.
        addresses = match_full_address(text)
        for address in addresses:
            # Match each name against the list of first and last names
            street_name = address[0].upper()
            house_number = address[1].upper() if address[1] else ''
            zip_code = address[2].upper() if address[2] else ''
            city = address[3].upper()if address[3] else ''

            street_address = u"%s %s" % (street_name, house_number)
            full_address = u"%s %s, %s %s" % (street_name, house_number,
                                              zip_code, city)

            if (street_address in self.whitelist or
                full_address in self.whitelist):
                continue
            blacklisted = (street_name in self.blacklist or
                           street_address in self.blacklist or
                           full_address in self.blacklist)
            street_match = street_name[:20] in self.street_names

            if blacklisted or (street_match and house_number):
                sensitivity = Sensitivity.HIGH
            elif street_match:
                # Real street name, but not blacklisted
                sensitivity = Sensitivity.LOW
            else:
                if zip_code or city:
                    # No real street name, but apparently an address
                    sensitivity = Sensitivity.OK
                else:
                    continue

            # Store the original matching text
            matched_text = address[4]

            # Update remaining, i.e. unmatched text
            unmatched_text = unmatched_text.replace(matched_text, "", 1)

            matches.add(
                MatchItem(matched_data=matched_text, sensitivity=sensitivity)
            )
        return matches
