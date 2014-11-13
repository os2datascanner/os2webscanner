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
import datetime


from django.conf import settings
from django.core.mail import EmailMessage
from django.template import loader, Context

import models


def notify_user(scan):
    """Notify user about completed scan - including success and failure."""
    template = 'os2webscanner/email/scan_report.html'

    t = loader.get_template(template)

    subject = "Scanning afsluttet: {0}".format(scan.status_text)
    to_addresses = [p.user.email for p in scan.scanner.recipients.all() if
                    p.user.email]
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


def scans_for_summary_report(summary, from_date=None, to_date=None):
    """Gather date for a summary report for a web page or an email."""
    # Calculate date period if not already given.
    # This would normally be called from cron with from_date = to_date = None.
    if not from_date:
        scd = summary.schedule
        # To initialize to a certain base
        scd.dtstart = datetime.datetime.utcfromtimestamp(0)
        from_date = scd.before(datetime.datetime.today() -
                               datetime.timedelta(days=1))

    if not to_date:
        to_date = datetime.datetime.today()

    relevant_scans = models.Scan.objects.filter(
        scanner__in=summary.scanners.all(),
        scanner__organization=summary.organization,
        start_time__gte=from_date,
        start_time__lt=to_date
    ).order_by('id')

    return (relevant_scans, from_date, to_date)


def send_summary_report(summary, from_date=None, to_date=None,
                        extra_email=None):
    """Send the actual summary report by email."""
    relevant_scans, from_date, to_date = scans_for_summary_report(
        summary,
        from_date,
        to_date
    )

    url = settings.SITE_URL

    c = Context({'scans': relevant_scans,
                 'from_date': from_date,
                 'to_date': to_date,
                 'summary': summary,
                 'site_url': url})
    template = 'os2webscanner/email/summary_report.html'

    t = loader.get_template(template)

    subject = "Opsummering fra webscanneren: {0}".format(summary.name)
    to_addresses = [p.user.email for p in summary.recipients.all() if
                    p.user.email]
    if not to_addresses:
        # TODO: In the end, of course, when no email addresses are found no
        # mail should be sent. This is just for debugging.
        to_addresses = ['carstena@magenta.dk', ]

    if extra_email:
        to_addresses.append(extra_email)
    try:
        body = t.render(c)
        message = EmailMessage(subject, body, settings.ADMIN_EMAIL,
                               to_addresses)
        message.content_subtype = "html"
        message.send()
        print "Mail sendt til", ",".join(to_addresses)
    except Exception as e:
        # TODO: Handle this properly
        raise


def dispatch_pending_summaries():
    """Find out if any summaries need to be sent out, do it if so."""
    summaries = models.Summary.objects.filter(do_email_recipients=True)

    for summary in summaries:
        # TODO: Check if this summary must be sent today, according to its
        # schedule.
        schedule = summary.schedule
        schedule.dtstart = datetime.datetime.utcfromtimestamp(0)
        today = datetime.datetime.today()
        # If today's a schedule day, "before" will give us 00:00 AM on the very
        # same day.
        maybe_today = schedule.before(today)

        if today.date() == maybe_today.date():
            send_summary_report(summary)
