#!/usr/bin/env python
# Include the Django app
import os
import sys
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"

import unittest
from scanner.rules import cpr, name

class NameTest(unittest.TestCase):
    def test_matching(self):
        """
        Test Name matching in text
        :return:
        """
        text = """
            Jens Jensen.
            Jim Smith.
            sdfsdsad Asdfsddsfasd
            """
        whitelist = """
        Jim Smith
        """
        valid_names = ['Jens Jensen']
        invalid_names = ['sdfsdsad Asdfsddsfasd', 'Jim Smith']
        matches = name.NameRule(whitelist=whitelist).execute(text)
        for valid_name in valid_names:
            print matches
            self.assertTrue(any(m['matched_data'] == valid_name for m in matches))
        for invalid_name in invalid_names:
            self.assertFalse(any(m['matched_data'] == invalid_name for m in matches))

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