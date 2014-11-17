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

""" Web service functions, to be invoked over XML-RPC."""

import os
import re
import StringIO
import csv
import tempfile

from django.contrib.auth import authenticate
from django.conf import settings

from .utils import do_scan
from .models import Match, Scan

from django_xmlrpc.decorators import xmlrpc_func


def scan_urls(username, password, urls):
    """Web service for scanning URLs specified by the caller.

    Parameters:
        * username (string) - login credentials
        * password (string) - login credentials
        * urls  (list of strings) - the URLs to be scanned.
    Return value:
        The URL for retrieving the report.
    """
    # First check the user sent us a list
    if not isinstance(urls, list):
        raise RuntimeError("Malformed parameters.")
    user = authenticate(username=username, password=password)
    if not user:
        raise RuntimeError("Wrong username or password!")
    scan = do_scan(user, urls)

    url = scan.get_absolute_url()
    return "{0}{1}".format(settings.SITE_URL, url)


def scan_documents(username, password, data):
    """Web service for scanning the documents send by the caller.

    Parameters:
        * username (string) - login credentials
        * password (string) - login credentials
        * data (list of tuples) - (binary, filename) the files to be scanned.
    Return value:
        The URL for retrieving the report.
    """
    # First check the user sent us a list
    if not isinstance(data, list):
        raise RuntimeError("Malformed parameters.")
    # Authenticate
    user = authenticate(username=username, password=password)
    if not user:
        raise RuntimeError("Wrong username or password!")

    dirname = tempfile.mkdtemp()
    # Save files on disk
    def writefile(data_item):
        binary, filename = data_item
        full_path = os.path.join(dirname, filename)
        with open(full_path, "wb") as f:
            f.write(binary.data)
        return full_path
    documents = map(writefile, data)
    file_url = lambda f: 'file://{0}'.format(f)
    scan = do_scan(user, map(file_url, documents))
    # map(os.remove, documents)

    url = scan.get_absolute_url()
    return "{0}{1}".format(settings.SITE_URL, url)


@xmlrpc_func(returns='list', args=['string', 'string', 'string'])
def get_status(username, password, report_url):
    """Web service for retrieving the status of a scan.

    The scan is identified by the report URL returned by the functions
    scan_urls and scan_documents.

    Parameters:
        * username
        * password
        * report_url - the output of one of the two "scan_" functions.
    Return value:
        A list on the form [status, start_time, end_time, number_of_matches].
    """
    user = authenticate(username=username, password=password)
    if not user:
        raise RuntimeError("Wrong username or password!")
    match_exp = "(?<=/)[0-9]+(?=/)"
    try:
        res = re.search(match_exp, report_url)
        id = int(res.group(0))
    except Exception:
        raise RuntimeError("Malformed URL")
    try:
        scan = Scan.objects.get(id=id)
    except Exception:
        raise RuntimeError("Report not found")

    count = Match.objects.filter(scan=scan).count()
    result = (
        scan.status_text, scan.start_time or '', scan.end_time or '', count
    )
    return result


def get_report(username, password, report_url):
    """Retrieve a report in CSV format, e.g. to parse or to save in a file.

    Parameters:
        * username
        * password
        * report_url - the output of one of the two "scan_" functions.

    Return value:
        A UTF-encoded string containing the CSV data separated by line breaks.
    """
    user = authenticate(username=username, password=password)
    if not user:
        raise RuntimeError("Wrong username or password!")
    match_exp = "(?<=/)[0-9]+(?=/)"
    try:
        res = re.search(match_exp, report_url)
        id = int(res.group(0))
    except Exception:
        raise RuntimeError("Malformed URL")
    try:
        scan = Scan.objects.get(id=id)
    except Exception:
        raise RuntimeError("Report not found")
    # We now have the scan object
    output = StringIO.StringIO()
    writer = csv.writer(output)

    all_matches = Match.objects.filter(scan=scan).order_by(
        '-sensitivity', 'url', 'matched_rule', 'matched_data'
    )
    # CSV utilities
    e = lambda fields: ([f.encode('utf-8') for f in fields])
    # Print summary header
    writer.writerow(e([u'Starttidspunkt', u'Sluttidspunkt', u'Status',
                    u'Totalt antal matches']))
    # Print summary
    writer.writerow(e([str(scan.start_time),
        str(scan.end_time), scan.get_status_display(),
        str(len(all_matches))]))
    # Print match header
    writer.writerow(e([u'URL', u'Regel', u'Match', u'Følsomhed']))
    for match in all_matches:
        writer.writerow(e([match.url.url,
                         match.get_matched_rule_display(),
                         match.matched_data.replace('\n', ''),
                         match.get_sensitivity_display()]))
    return output.getvalue()
