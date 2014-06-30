#!/usr/bin/env python
# Include the Django app
import os
import sys
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"

import unittest
from scanner.rules import cpr, name
from scanner.scanner.scanner import Scanner
import re

class ScannerTest(unittest.TestCase):
    def test_scanner(self):
        scanner = Scanner(rules = [cpr.CPRRule()], domains = [])
        data = """Blah blah 211062-5629 Blah blah."""
        scanner.scan(data, matches_callback=self.matches_callback)

    def matches_callback(self, matches):
        self.assertTrue("2110XXXXXX" in [m['matched_data'] for m in matches])

class NameTest(unittest.TestCase):
    def test_matching(self):
        """
        Test Name matching in text
        :return:
        """
        text = """
            Jens Jensen
            Jim Smith Jones
            sdfsdsad Asdfsddsfasd
            """
        # whitelist = """
        # Jim Smiths
        # """
        valid_names = ['Jens Jensen', 'Jensen Jim', 'Jim Smith', 'Jens Jensen Jim', 'Jensen Jim Smith', 'Jens Jensen Jim Smith',
                       'Smith Jones', 'Jim Smith Jones', 'Jensen Jim Smith Jones']
        invalid_names = ['sdfsdsad Asdfsddsfasd']
        matches = name.NameRule().execute(text)
        matches = [re.sub('\s+', ' ', m['matched_data']) for m in matches]
        print matches
        for valid_name in valid_names:
            self.assertTrue(any(m == valid_name for m in matches))
        for invalid_name in invalid_names:
            self.assertFalse(any(m == invalid_name for m in matches))

class CPRTest(unittest.TestCase):
    def test_matching(self):
        """
        Test CPR matching in text
        :return:
        """
        text = """
            211062-5629
            4110625629
            6113625629
            911062 5629
            """
        valid_cprs = ['2110625629']
        invalid_cprs = ['4110625629', '2113625629', '9110625629']

        matches = cpr.match_cprs(text, mask_digits = False)

        for valid_cpr in valid_cprs:
            self.assertTrue(any(m['matched_data'] == valid_cpr for m in matches))
        for invalid_cpr in invalid_cprs:
            self.assertFalse(any(m['matched_data'] == invalid_cpr for m in matches))


def main():
    unittest.main()

if __name__ == '__main__':
    main()