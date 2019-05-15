import os
import sys
import unittest
import django

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(os.path.join(__file__, "../../../"))))
print('\n===Base dir: ' + base_dir)
print('\n===Current working dir: ' + os.getcwd())
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "os2datascanner.sites.admin.settings"
django.setup()

from os2webscanner.models.organization_model import Organization
from os2webscanner.models.regexrule_model import RegexRule
from os2webscanner.models.regexpattern_model import RegexPattern
from os2webscanner.models.sensitivity_level import Sensitivity
from os2webscanner.models.webdomain_model import WebDomain
from os2webscanner.models.webscanner_model import WebScanner

from django.conf import settings
from subprocess import Popen, STDOUT, PIPE


class ScannerTest(unittest.TestCase):

    def setUp(self):
        """
        Setup some data to test with.
        """

        # create organisations
        self.magenta_org = Organization(name="Magenta", pk=1)
        self.magenta_org.save()
        self.theydontwantyouto_org = Organization(name="TheyDontWantYouTo", pk=2)
        self.theydontwantyouto_org.save()
        # create Webdomains
        self.magenta_domain = WebDomain(url="http://magenta.dk", organization=self.magenta_org,
                                        validation_status=WebDomain.VALID, download_sitemap=False)
        self.theydontwantyouto_domain = WebDomain(url="http://theydontwantyou.to",
                                                  organization=self.theydontwantyouto_org,
                                                  validation_status=WebDomain.VALID, download_sitemap=False)
        self.magenta_domain.save()
        self.theydontwantyouto_domain.save()
        # create Rules and rulesets
        self.reg1 = RegexPattern(pattern_string='fællesskaber', pk=1)
        self.reg2 = RegexPattern(pattern_string='Ombudsmand', pk=2)
        self.reg3 = RegexPattern(pattern_string='projektnetwerk', pk=3)
        self.reg4 = RegexPattern(pattern_string='secure', pk=4)
        self.reg5 = RegexPattern(pattern_string='control', pk=5)
        self.reg6 = RegexPattern(pattern_string='breathe', pk=6)
        self.reg1.save()
        self.reg2.save()
        self.reg3.save()
        self.reg4.save()
        self.reg5.save()
        self.reg6.save()

        # Create rule sets
        self.tr_set1 = RegexRule(name='MagentaTestRule1', sensitivity=Sensitivity.OK, organization=self.magenta_org,
                                 pk=1)
        self.tr_set2 = RegexRule(name='TheyDontWantYouToKnow', sensitivity=Sensitivity.OK,
                                 organization=self.theydontwantyouto_org, pk=2)
        self.tr_set1.save()
        self.tr_set2.save()
        self.tr_set1.patterns.add(self.reg1)
        self.tr_set1.patterns.add(self.reg2)
        self.tr_set1.patterns.add(self.reg3)
        self.tr_set2.patterns.add(self.reg4)
        self.tr_set1.save()
        self.tr_set2.save()

    def test_run_scan(self):
        """
        Test running a scan.
        """

        scanner = WebScanner(name='MagentaTestScan', organization=self.magenta_org, pk=1)
        scanner.save()
        scanner.regex_rules.add(self.tr_set1)
        scanner.domains.add(self.magenta_domain)

        SCRAPY_WEBSCANNER_DIR = os.path.join(settings.PROJECT_DIR, "scrapy-webscanner")
        LOG_FILE_U = os.path.join(settings.PROJECT_DIR, 'var', 'logs',  'scans', 'scan_1.log')

        log_file = open(LOG_FILE_U, "a")

        result = scanner.run()

        try:
            process = Popen([os.path.join(SCRAPY_WEBSCANNER_DIR, "run.sh"),
                             str(scanner.pk)], cwd=SCRAPY_WEBSCANNER_DIR,
                            stderr=log_file,
                            stdout=log_file)
            # stdout, stderr = process.communicate()

        except Exception as e:
            print(e)
            return None

        # self.assertTrue(isinstance(result, Scan))

        stdout, stderr = process.communicate()

def main():
    """Run the unit tests."""
    unittest.main()


if __name__ == '__main__':
    main()
