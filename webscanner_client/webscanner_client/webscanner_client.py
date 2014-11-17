"""Webscanner client API class."""

import os
import xmlrpclib


class WebscannerClient(object):

    """Client for the OS2 web scanner."""

    def __init__(self, url, verbose=False):
        """Set up server proxy."""
        self._url = url
        rpc_args = {'verbose': verbose, 'allow_none': True}

        self._rpc_srv = xmlrpclib.ServerProxy(self._url, **rpc_args)

    def scan_urls(self, user, password, urls):
        """Scan given URLs with the user credentials provided."""
        return self._rpc_srv.scan_urls(user, password, urls)

    def scan_documents(self, user, password, documents):
        """Scan documents in list, upload to server for scan."""
        def get_binary(path):
            with open(path, "rb") as f:
                return xmlrpclib.Binary(f.read())
        docs = map(get_binary, documents)
        filenames = map(os.path.basename, documents)
        data = zip(docs, filenames)
        
        return self._rpc_srv.scan_documents(user, password, data)

    def get_status(self, user, password, report_url):
        """Get status for given report."""
        return self._rpc_srv.get_status(user, password, report_url)

    def get_report(self, user, password, report_url):
        """Retrieve report from server."""
        return self._rpc_srv.get_report(user, password, report_url)
