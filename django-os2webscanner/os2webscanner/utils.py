# encoding: utf-8
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

import os
import shutil
import requests
import time
import datetime
import chardet
import logging

from django.db import IntegrityError
from django.conf import settings
from django.core.mail import EmailMessage
from django.template import loader

from os2webscanner.models.match_model import Match
from os2webscanner.models.url_model import Url
from os2webscanner.models.scannerjobs.scanner_model import Scanner
from os2webscanner.models.scans.scan_model import Scan
from os2webscanner.models.summary_model import Summary


def notify_user(scan):
    """Notify user about completed scan - including success and failure."""
    template = 'os2webscanner/email/scan_report.html'

    t = loader.get_template(template)

    to_addresses = [p.user.email for p in scan.scanner.recipients.all() if
                    p.user.email]
    if not to_addresses:
        to_addresses = [settings.ADMIN_EMAIL, ]
    matches = Match.objects.filter(scan=scan).count()
    matches += Url.objects.filter(
        scan=scan
    ).exclude(status_code__isnull=True).count()
    critical = scan.no_of_critical_matches

    scan_status = ''
    if scan.no_of_critical_matches > 0:
        scan_status = "Kritiske matches!"
    elif hasattr(scan, 'webscan'):
        if scan.webscan.no_of_broken_links > 0:
            scan_status = "Døde links"
    else:
        if scan.status_text:
            scan_status = scan.status_text
        else:
            scan_status = 'Ingen status tekst.'

    subject = "Scanning afsluttet: {0}".format(scan_status)

    c = {'scan': scan, 'domain': settings.SITE_URL,
         'matches': matches, 'critical': critical}

    if scan.scanner.organization.do_notify_all_scans or critical > 0:
        try:
            body = t.render(c)
            message = EmailMessage(subject, body, settings.ADMIN_EMAIL,
                                   to_addresses)
            message.send()
        except Exception:
            # TODO: Handle this properly
            raise


def capitalize_first(s):
    """Capitalize the first letter of a string, leaving the others alone."""
    if s is None or len(s) < 1:
        return ""
    return s.replace(s[0], s[0].upper(), 1)


def get_supported_rpc_params():
    """Return a list of supported Scanner parameters for the RPC interface."""
    return ["do_cpr_scan", "do_cpr_modulus11",
            "do_cpr_ignore_irrelevant", "do_ocr", "do_name_scan",
            "output_spreadsheet_file", "do_cpr_replace", "cpr_replace_text",
            "do_name_replace", "name_replace_text", "do_address_scan",
            "do_address_replace", "address_replace_text", "columns"]


def do_scan(user, urls, params={}, blocking=False, visible=False, add_domains=True):
    """Create a scanner to scan a list of URLs.

    The 'urls' parameter may be either http:// or file:// URLS - we expect the
    scanner to handle this distinction transparently. The list is assumed to be
    well-formed and denote existing files/URLs. The consequences of load errors
    etc. should be in the report.

    The 'params' parameter should be a dict of supported Scanner
    parameters and values. Defaults are used for unspecified parameters.
    """
    scanner = Scanner()
    scanner.organization = user.profile.organization

    scanner.name = user.username + '-' + str(time.time())
    scanner.do_run_synchronously = True
    # TODO: filescan does not contain these properties.
    scanner.do_last_modified_check = False
    scanner.do_last_modified_check_head_request = False
    scanner.process_urls = urls
    scanner.is_visible = visible

    supported_params = get_supported_rpc_params()
    for param in params:
        if param in supported_params:
            setattr(scanner, param, params[param])
        else:
            raise ValueError("Unsupported parameter passed: " + param +
                             ". Supported parameters: " +
                             str(supported_params))

    scanner.save()

    if add_domains:
        for domain in scanner.organization.domains.all():
            scanner.domains.add(domain)
    scan = scanner.run(user=user, blocking=blocking)
    # NOTE: Running scan may have failed.
    # Pass the error message or empty scan in that case.

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

    relevant_scans = Scan.objects.filter(
        scanner__in=summary.scanners.all(),
        scanner__organization=summary.organization,
        start_time__gte=from_date,
        start_time__lt=to_date
    ).order_by('id')

    return relevant_scans, from_date, to_date


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
        to_addresses = ['ann@magenta.dk', ]

    if extra_email:
        to_addresses.append(extra_email)
    try:
        body = t.render(c)
        message = EmailMessage(subject, body, settings.ADMIN_EMAIL,
                               to_addresses)
        message.content_subtype = "html"
        message.send()
        summary.last_run = datetime.datetime.now()
        summary.save()
    except Exception:
        # TODO: Handle this properly
        raise


def dispatch_pending_summaries():
    """Find out if any summaries need to be sent out, do it if so."""
    summaries = Summary.objects.filter(do_email_recipients=True)

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


def get_failing_urls(scan_id, target_directory):
    """Retrieve the physical document that caused conversion errors."""
    source_file = os.path.join(
            settings.VAR_DIR,
            "logs/scans/occurrence_{0}.log".format(scan_id)
            )
    with open(source_file, "r") as f:
        lines = f.readlines()

    urls = [l.split("URL: ")[1].strip() for l in lines if l.find("URL") >= 0]

    for u in set(urls):
        f = requests.get(u, stream=True)
        target = os.path.join(
                target_directory,
                u.split('/')[-1].split('#')[0].split('?')[0]
                )
        with open(target, 'wb') as local_file:
            shutil.copyfileobj(f.raw, local_file)


def get_codec_and_string(bytestring, encoding="utf-8"):
    """ Get actual encoding and stringdata from bytestring
        use UnicodeDammit if this  doesn't work
        https://www.crummy.com/software/BeautifulSoup/bs4/doc/#unicode-dammit
    """ 
    try:
        stringdata = bytestring.decode(encoding)
    except AttributeError:
        # no decode - is a string
        return None, bytestring
    except UnicodeDecodeError:
        encoding = chardet.detect(bytestring).get('encoding')
        if encoding is not None:
            stringdata = bytestring.decode(encoding)
        else:
            raise

    return encoding, stringdata


def secure_save(object):
    try:
       object.save()
    except IntegrityError as ie:
       logging.error('Error Happened: {}'.format(ie))


def domain_form_manipulate(form):
    """ Manipulates domain form fields.
    All form widgets will have added the css class 'form-control'.
    All domain names must be without spaces.
    """
    for fname in form.fields:
        f = form.fields[fname]
        f.widget.attrs['class'] = 'form-control'

    if form['url'].value():
        if ' ' in form['url'].value():
            form.add_error('url', u'Mellemrum er ikke tilladt i domænenavnet.')

    return form
