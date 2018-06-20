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
import csv
import tempfile

from django.contrib.auth import authenticate
from django.conf import settings
from django.utils import six

from .utils import do_scan
from .models.match_model import Match
from .models.scan_model import Scan

from django_xmlrpc.decorators import xmlrpc_func


@xmlrpc_func(returns='string', args=['string', 'string', 'string', 'dict'])
def scan_urls(username, password, urls, params={}):
    """Web service for scanning URLs specified by the caller.

    Parameters:
        * username (string) - login credentials
        * password (string) - login credentials
        * urls  (list of strings) - the URLs to be scanned.
        * params (dict) - parameters for the scanner.
    Return value:
        The URL for retrieving the report.
    """
    # Authenticate
    user = authenticate(username=username, password=password)
    if not user:
        raise RuntimeError("Wrong username or password!")
    do_scan(user, urls, params)

    return do_scan_urls(user, urls, params)


@xmlrpc_func(returns='string', args=['string', 'string', 'string', 'dict'])
def scan_documents(username, password, data, params={}):
    """Web service for scanning the documents sent by the caller.

    Parameters:
        * username (string) - login credentials
        * password (string) - login credentials
        * data (list of tuples) - (binary, filename) the files to be scanned.
        * params (dict) - parameters for the scanner.
    Return value:
        The URL for retrieving the report.
    """
    # Authenticate
    user = authenticate(username=username, password=password)
    if not user:
        raise RuntimeError("Wrong username or password!")

    return do_scan_documents(user, data, params)


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
    output = six.moves.StringIO()
    writer = csv.writer(output)

    all_matches = Match.objects.filter(scan=scan).order_by(
        '-sensitivity', 'url', 'matched_rule', 'matched_data'
    )
    # CSV utilities
    e = lambda fields: ([f.encode('utf-8') for f in fields])
    # Print summary header
    writer.writerow(e(['Starttidspunkt', 'Sluttidspunkt', 'Status',
                    'Totalt antal matches']))
    # Print summary
    writer.writerow(
        e([str(scan.start_time),
           str(scan.end_time), scan.get_status_display(),
           str(len(all_matches))])
    )
    # Print match header
    writer.writerow(e(['URL', 'Regel', 'Match', 'Følsomhed']))
    for match in all_matches:
        writer.writerow(
            e([match.url.url,
               match.get_matched_rule_display(),
               match.matched_data.replace('\n', '').replace('\r', ' '),
               match.get_sensitivity_display()]))
    return output.getvalue()


def do_scan_urls(user, urls, params={}):
    """Implementation of scan_urls for direct calling."""
    # Check parameters
    if not isinstance(urls, list):
        raise RuntimeError("Malformed parameters.")
    if not isinstance(params, dict):
        raise RuntimeError("Malformed params parameter.")
    scan = do_scan(user, urls, params)

    url = scan.get_absolute_url()
    return "{0}{1}".format(settings.SITE_URL, url)


def do_scan_documents(user, data, params={}):
    """Implementation of scan_documents for direct calling."""
    # Check parameters
    if not isinstance(data, list):
        raise RuntimeError("Malformed parameters.")
    if not isinstance(params, dict):
        raise RuntimeError("Malformed params parameter.")

    # Create RPC dir for temp files
    rpcdir = settings.RPC_TMP_PREFIX
    try:
        os.makedirs(rpcdir)
    except OSError:
        if os.path.isdir(rpcdir):
            pass
        else:
            # There was an error, so make sure we know about it
            raise
    # Now create temporary dir, fill with files
    dirname = tempfile.mkdtemp(dir=rpcdir)

    # Save files on disk
    def writefile(data_item):
        binary_decoder = xmlrpclib.Binary()
        binary, filename = data_item
        binary_decoder.decode(binary)
        full_path = os.path.join(dirname, filename)
        with open(full_path, "wb") as f:
            f.write(binary_decoder.data)
        return full_path
    documents = list(map(writefile, data))
    file_url = lambda f: 'file://{0}'.format(f)
    scan = do_scan(user, list(map(file_url, documents)), params, blocking=True)
    # map(os.remove, documents)
    if not isinstance(scan, Scan):
        raise RuntimeError("Unable to perform scan - check user has" +
                           "organization and valid domain")
    url = scan.get_absolute_url()
    return "{0}{1}".format(settings.SITE_URL, url)
