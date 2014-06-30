# coding=utf-8
import regex
import os
import codecs

from scrapy import log
from rule import Rule
from os2webscanner.models import Sensitivity, Match

name_regexs = [
    # Match First Last
    regex.compile("\\b(?P<first>\\p{Uppercase}\\p{Lowercase}+)\\s+(?P<last>\\p{Uppercase}\\p{Lowercase}+)\\b",
                  regex.UNICODE),
    # Match First Middle Last
    regex.compile(
        "\\b(?P<first>\\p{Uppercase}\\p{Lowercase}+)(?P<middle>(\\s+\\p{Uppercase}(\\p{Lowercase}+|\\.)))\\s+(?P<last>\\p{Uppercase}\\p{Lowercase}+)\\b",
        regex.UNICODE),
    # Match First Middle Middle Last
    regex.compile(
        "\\b(?P<first>\\p{Uppercase}\\p{Lowercase}+)(?P<middle>(\\s+\\p{Uppercase}(\\p{Lowercase}+|\\.)){2})\\s+(?P<last>\\p{Uppercase}\\p{Lowercase}+)\\b",
        regex.UNICODE)]


def match_name(text):
    matches = set()
    for name_regex in name_regexs:
        it = name_regex.finditer(text, overlapped=True)
        for m in it:
            first = m.group("first")
            try:
                middle = m.group("middle")
            except IndexError:
                middle = ''
            if middle != '':
                middle_split = tuple(regex.split('\s+', middle.lstrip(), regex.UNICODE))
            else:
                middle_split = None
            last = m.group("last")
            matched_text = m.group(0)
            matches.add((first, middle_split, last, matched_text))
    return matches


def load_name_file(file_name):
    """
    Load a data file containing persons names in uppercase, separated by a tab
    character followed by a number, one per line.

    The file is of the format:
    NAME\t12312
    Return a list of all the names in unicode
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
    Returns a set of the names in all upper-case characters"""
    return set([line.upper().strip() for line in whitelist.splitlines()])


class NameRule(Rule):
    name = 'name'
    _data_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))) + '/data'
    _last_name_file = 'efternavne_2014.txt'
    _first_name_files = ['fornavne_2014_-_kvinder.txt', 'fornavne_2014_-_mænd.txt']

    def __init__(self, whitelist=None):
        # Load first and last names from data files
        self.last_names = load_name_file(self._data_dir + '/' + self._last_name_file)
        self.first_names = []
        for f in self._first_name_files:
            self.first_names.extend(load_name_file(self._data_dir + '/' + f))

        # Convert to sets for efficient lookup
        self.last_names = set(self.last_names)
        self.first_names = set(self.first_names)
        if whitelist is not None:
            self.whitelist = load_whitelist(whitelist)
        else:
            self.whitelist = set()

    def execute(self, text):
        names = match_name(text)
        matches = set()
        for name in names:
            # Match each name against the list of first and last names
            first_name = name[0].upper()
            last_name = name[2].upper()

            if u"%s %s" % (first_name, last_name) in self.whitelist:
                continue

            first_match = first_name in self.first_names
            last_match = last_name in self.last_names

            # Set sensitivity according to how many of the names were found
            # in the names lists
            if first_match and last_match:
                sensitivity = Sensitivity.HIGH
            elif first_match or last_match:
                sensitivity = Sensitivity.LOW
            else:
                sensitivity = Sensitivity.OK

            # TODO: Also check middle name(s)?

            # Store the original matching text
            matched_text = name[3]

            matches.add(Match(matched_data=matched_text, sensitivity=sensitivity))
        return matches
