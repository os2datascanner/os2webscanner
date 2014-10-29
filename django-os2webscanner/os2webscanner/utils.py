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

"""Utility methods for the OS2Webscanner project."""

import time

from django.conf import settings
from django.core.mail import EmailMessage
from django.template import loader, Context


def notify_user(scan):
    """Notify user about completed scan - including success and failure."""
    template = 'os2webscanner/email/scan_report.html'

    t = loader.get_template(template)

    subject = "Scanning afsluttet: {0}".format(scan.status_text)
    to_addresses = [p.user.email for p in scan.recipients.all() if
                    p.user.email]
    print to_addresses
    if not to_addresses:
        to_addresses = [settings.ADMIN_EMAIL, ]
    matches = models.Match.objects.filter(scan=scan).count()
    matches += models.Url.objects.filter(
        scan=scan
    ).exclude(status_code__isnull=True).count()
    critical = models.Match.objects.filter(
        scan=scan,
        sensitivity=models.Sensitivity.HIGH
    ).count()

    c = Context({'scan': scan, 'domain': settings.SITE_URL, 'matches': matches,
                 'critical': critical})

    try:
        body = t.render(c)
        message = EmailMessage(subject, body, settings.ADMIN_EMAIL,
                               to_addresses)
        message.send()
        print "Mail sendt til", ",".join(to_addresses)
    except Exception as e:
        # TODO: Handle this properly
        raise


def capitalize_first(s):
    """Capitalize the first letter of a string, leaving the others alone."""
    if s is None or len(s) < 1:
        return u""
    return s.replace(s[0], s[0].upper(), 1)

import models


def do_scan(user, urls):
    """Create a scanner to scan a list of URLs.

    The 'urls' parameter may be either http:// or file:// URLS - we expect the
    scanner to handle this distinction transparently. The list is assumed to be
    well-formed and denote existing files/URLs. The consequences of load errors
    etc. should be in the report.
    """
    # TODO: Scan the listed URLs and return result to user
    scanner = models.Scanner()
    scanner.organization = user.get_profile().organization
    scanner.name = user.username + '-' + str(time.time())
    scanner.do_run_synchronously = True
    scanner.process_urls = urls
    scanner.is_visible = False

    scanner.save()
    for domain in scanner.organization.domains.all():
        scanner.domains.add(domain)
    scanner.run(user=user)

    scan = scanner.scans.all()[0]
    return scan
