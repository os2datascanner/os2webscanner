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
_name = "{0}(-{0})?".format(_simple_name)
full_name_regex = regex.compile(
    "\\b(?P<first>" + _name + ")" +
    "(?P<middle>(" + _whitespace + _name + "){0,3})" +
    "(?P<last>" + _whitespace + _name + "){1}\\b", regex.UNICODE)


def match_full_name(text):
    """Return possible name matches in the given text."""
    matches = set()
    it = full_name_regex.finditer(text, overlapped=False)
    for m in it:
        first = m.group("first")
        try:
            middle = m.group("middle")
        except IndexError:
            middle = ''
        if middle != '':
            middle_split = tuple(
                regex.split('\s+', middle.lstrip(), regex.UNICODE))
        else:
            middle_split = ()
        last = m.group("last").lstrip()
        matched_text = m.group(0)
        matches.add((first, middle_split, last, matched_text))
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
        # Skip beginning lines which are not in uppercase
        if len(line) > 0 and not line[1].isupper():
            continue
        names.append(unicode(line[:line.index('\t')]))
    return names


def load_whitelist(whitelist):
    """Load a list of names from a multi-line string, one name per line.

    Returns a set of the names in all upper-case characters
    """
    return set(
        [
            line.upper().strip() for line in whitelist.splitlines()
        ] if whitelist else []
    )


class NameRule(Rule):

    """Represents a rule which scans for Full Names in text.

    The rule loads a list of names from first and last name files and matches
    names against them to determine the sensitivity level of the matches.
    Matches against full, capitalized, names with up to 2 middle names.
    """

    name = 'name'
    _data_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__)))) + '/data'
    _last_name_file = 'efternavne_2014.txt'
    _first_name_files = ['fornavne_2014_-_kvinder.txt',
                         'fornavne_2014_-_mænd.txt']

    def __init__(self, whitelist=None, blacklist=None):
        """Initialize the rule with optional whitelist and blacklist.

        The whitelist should contains a multi-line string, with one name per
        line.
        """
        # Load first and last names from data files
        self.last_names = load_name_file(
            self._data_dir + '/' + self._last_name_file)
        self.first_names = []
        for f in self._first_name_files:
            self.first_names.extend(load_name_file(self._data_dir + '/' + f))

        # Convert to sets for efficient lookup
        self.last_names = set(self.last_names)
        self.first_names = set(self.first_names)
        self.all_names = self.last_names.union(self.first_names)
        self.whitelist = load_whitelist(whitelist)
        self.blacklist = load_whitelist(blacklist)

    def execute(self, text):
        """Execute the Name rule."""
        matches = set()
        unmatched_text = text
        # Determine if a name matches one of the lists
        match = lambda n, list: n in self.blacklist or (n in list and not
                                                        n in self.whitelist)

        # First, check for whole names, i.e. at least Firstname + Lastname
        names = match_full_name(text)
        for name in names:
            # Match each name against the list of first and last names
            first_name = name[0].upper()
            middle_names = [n.upper() for n in name[1]]
            last_name = name[2].upper() if name[2] else ""
            if middle_names:
                full_name = u"%s %s" % (first_name, last_name)
            else:
                full_name = u"%s %s %s" % (
                    first_name, " ".join(middle_names), last_name
                )
            if full_name in self.whitelist:
                continue
            first_match = match(first_name, self.first_names)
            last_match = match(last_name, self.last_names)
            middle_match = any(
                [match(n, self.all_names) for n in middle_names]
            )

            # Check if name is blacklisted.
            # The name is blacklisted if there exists a string in the
            # blacklist which is contained as a substring of the name.
            is_match = lambda str: str in full_name
            is_blacklisted = any(map(is_match, self.blacklist))
            # Name match is always high sensitivity
            # and occurs only when first and last name are in the name lists
            # Set sensitivity according to how many of the names were found
            # in the names lists
            if (first_match and last_match) or is_blacklisted:
                sensitivity = Sensitivity.HIGH
            elif first_match or last_match or middle_match:
                sensitivity = Sensitivity.LOW
            else:
                #sensitivity = Sensitivity.OK
                continue

            # Store the original matching text
            matched_text = name[3]

            # Update remaining, i.e. unmatched text
            unmatched_text = unmatched_text.replace(matched_text, "", 1)

            matches.add(
                MatchItem(matched_data=matched_text, sensitivity=sensitivity)
            )
        # Full name match done. Now check if there's any standalone names in
        # the remaining, i.e. so far unmatched string.
        name_regex = regex.compile(_name)
        it = name_regex.finditer(unmatched_text, overlapped=False)
        for m in it:
            matched = m.group(0)
            if match(matched.upper(), self.all_names):
                # Check blacklist - only exact matches
                if matched.upper() in self.blacklist:
                    sensitivity = Sensitivity.HIGH
                else:
                    sensitivity = Sensitivity.HIGH
                matches.add(
                    MatchItem(matched_data=matched,
                              sensitivity=Sensitivity.LOW)
                )
        return matches
