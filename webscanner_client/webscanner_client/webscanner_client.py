import os
import xmlrpclib
import urllib2


class WebscannerClient(object):
    """Client for the OS2 web scanner."""

    def __init__(self, url, verbose=False):
        """Set up server proxy."""
        self._url = url
        rpc_args = {'verbose': verbose, 'allow_none': True}

        self._rpc_srv = xmlrpclib.ServerProxy(self._url, **rpc_args)

    def scan_urls(self, user, password, urls):
        return self._rpc_srv.scan_urls(user, password, urls)

    def scan_documents(self, user, password, documents):
        # TODO: Figure out how to send documents to server
        return self._rpc_srv.scan_documents(user, password, documents)
