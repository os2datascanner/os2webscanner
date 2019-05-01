import csv
import os
import sys
import django

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(os.path.join(__file__, "../../"))))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"
django.setup()

from os2webscanner.models.organization_model import Organization
from os2webscanner.models.webdomain_model import WebDomain

# get organization
organization = Organization.objects.get(pk=1)
# take sys arg which is path to csv file
filepath = sys.argv[1]
# load csv file
with open(filepath, newline='') as csvfile:
        domain_reader = csv.reader(csvfile, delimiter=';')
        for domain in domain_reader:
            print('Domain: {}'.format(domain[0]))
            # insert values
            WebDomain.objects.create(url=domain[0],
                                     organization=organization,
                                     validation_status=1,
                                     download_sitemap=False)
