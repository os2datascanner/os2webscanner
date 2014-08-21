# Web service functions, to be invoked over XML-RPC

import os
import time
import tempfile

from .models import Scanner

from django.contrib.auth import authenticate


def do_scan(user, urls):
    """Create a scanner to scan a list of URLs.

    The 'urls' parameter may be either http:// or file:// URLS - we expect the
    scanner to handle this distinction transparently. The list is assumed to be
    well-formed and denote existing files/URLs. The consequences of load errors
    etc. should be in the report.
    """
    # TODO: Scan the listed URLs and return result to user
    scanner = Scanner()
    scanner.organization = user.get_profile().organization
    scanner.name = user.username + '-' + str(time.time())
    scanner.do_run_synchronously = True
    scanner.process_urls = urls

    scanner.save()
    for domain in scanner.organization.domains.all():
        scanner.domains.add(domain)
    scanner.run()

    # TODO: Figure out how to present result
    return 0


def scan_urls(username, password, urls):
    """Web service for scanning URLs specified by the caller.

    Parameters:
        * username (string) - login credentials
        * password (string) - login credentials
        * urls  (list of strings) - the URLs to be scanned.
    """
    # First check the user sent us a list
    if not isinstance(urls, list):
        raise RuntimeError("Malformed parameters.")
    # Authenticate
    user = authenticate(username=username, password=password)
    if not user:
        raise RuntimeError("Wrong username or password!")

    return do_scan(user, urls)


def scan_documents(username, password, binary_documents):
    """Web service for scanning the documents send by the caller.

    Parameters:
        * username (string) - login credentials
        * password (string) - login credentials
        * binary_documents  (list of data) - the files to be scanned.
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
    result = do_scan(user, map(file_url, documents))
    # Assuming scan was synchronous, we can now clean up files
    map(os.remove, documents)

    return result
