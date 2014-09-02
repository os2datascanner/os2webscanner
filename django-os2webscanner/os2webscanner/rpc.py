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


def scan_documents(username, password, binary_documents):
    """Web service for scanning the documents send by the caller.

    Parameters:
        * username (string) - login credentials
        * password (string) - login credentials
        * binary_documents  (list of data) - the files to be scanned.
    Return value:
        The URL for retrieving the report.
    """
    # First check the user sent us a list
    if not isinstance(binary_documents, list):
        raise RuntimeError("Malformed parameters.")
    # Authenticate
    user = authenticate(username=username, password=password)
    if not user:
        raise RuntimeError("Wrong username or password!")

    # Save files on disk
    def writefile(binary_doc):
        handle, filename = tempfile.mkstemp()
        os.write(handle, binary_doc.data)
        return filename

    documents = map(writefile, binary_documents)
    file_url = lambda f: 'file://{0}'.format(f)
    scan = do_scan(user, map(file_url, documents))
    # Assuming scan was synchronous, we can now clean up files
    map(os.remove, documents)

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
