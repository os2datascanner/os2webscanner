import xmlrpclib


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
        def get_binary(path):
            with open(path, "rb") as f:
                return xmlrpclib.Binary(f.read())
        binary_docs = map(get_binary, documents)
        return self._rpc_srv.scan_documents(user, password, binary_docs)

    def get_status(self, user, password, report_url):
        return self._rpc_srv.get_status(user, password, report_url)

    def get_report(self, user, password, report_url):
        return self._rpc_srv.get_report(user, password, report_url)
