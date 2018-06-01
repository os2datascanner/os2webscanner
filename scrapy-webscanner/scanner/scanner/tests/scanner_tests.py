import os
import sys
import ipdb
from django.test import TestCase
import unittest
import django

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(os.path.join(__file__, "../../../"))))
print('\n===Base dir: ' + base_dir)
print('\n===Current working dir: ' + os.getcwd())
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"
django.setup()

from os2webscanner.models.organization_model import Organization
from os2webscanner.models.regexrule_model import RegexRule
from os2webscanner.models.rulesset_model import RulesSet
from os2webscanner.models.sensitivity_level import Sensitivity
from os2webscanner.models.webdomain_model import WebDomain
from os2webscanner.models.webscanner_model import WebScanner
from os2webscanner.models.scan_model import Scan


class ScannerTest(unittest.TestCase):

    def setUp(self):
        """
        Setup some data to test with.
        """

        ipdb.launch_ipdb_on_exception()
        # create organisations
        self.magenta_org = Organization(name="Magenta", pk=1)
        self.magenta_org.save()
        self.theydontwantyouto_org = Organization(name="TheyDontWantYouTo", pk=2)
        self.theydontwantyouto_org.save()
        # create Webdomains
        self.magenta_domain = WebDomain(url="http://magenta.dk", organization=self.magenta_org,
                                        validation_status=WebDomain.VALID, download_sitemap=False)
        self.theydontwantyouto_domain = WebDomain(url="", organization=self.theydontwantyouto_org,
                                                  validation_status=WebDomain.VALID, download_sitemap=False)
        self.magenta_domain.save()
        self.theydontwantyouto_domain.save()
        # create Rules and rulesets
        self.reg1 = RegexRule(name='TestRegex1', organization=self.magenta_org, match_string='leverer', pk=1)
        self.reg2 = RegexRule(name='TestRegex2', organization=self.magenta_org, match_string='Magenta', pk=2)
        self.reg3 = RegexRule(name='TestRegex3', organization=self.magenta_org, match_string='utraditionelt', pk=3)
        self.reg4 = RegexRule(name='TestRegex4', organization=self.theydontwantyouto_org, match_string='correspond',
                              pk=4)
        self.reg5 = RegexRule(name='TestRegex5', organization=self.theydontwantyouto_org, match_string='empowers', pk=5)
        self.reg6 = RegexRule(name='TestRegex6', organization=self.theydontwantyouto_org, match_string='vendor', pk=6)
        self.reg1.save()
        self.reg2.save()
        self.reg3.save()
        self.reg4.save()
        self.reg5.save()
        self.reg6.save()
        rset1 = [self.reg1, self.reg2, self.reg3]
        rset2 = [self.reg4, self.reg5, self.reg6]

        # Create rule sets
        self.tr_set1 = RulesSet(name='MagentaTRSet', sensitivity=Sensitivity.OK, pk=1)
        self.tr_set2 = RulesSet(name='TheyDontWantYouToTRSet', sensitivity=Sensitivity.OK, pk=2)
        self.tr_set1.save()
        self.tr_set2.save()
        self.tr_set1.regexrules.add(self.reg1)
        self.tr_set1.regexrules.add(self.reg2)
        self.tr_set1.regexrules.add(self.reg3)
        self.tr_set2.regexrules.add(self.reg4)

    def test_run_scan(self):
        """
        Test running a scan.
        """

        ipdb.launch_ipdb_on_exception()
        scanner = WebScanner(name='MagentaTestScan', organization=self.magenta_org)
        scanner.save()
        scanner.rules_sets.add(self.tr_set1)
        scanner.domains.add(self.magenta_domain)
        result = scanner.run()
        # ipdb.set_trace()
        self.assertTrue(isinstance(result, Scan))


def main():
    """Run the unit tests."""
    unittest.main()


if __name__ == '__main__':
    main()
