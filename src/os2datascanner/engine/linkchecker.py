"""A link checker using urllib2."""

import ssl
import socket
import urllib.request
import urllib.error
import urllib.parse
import http.client

import regex
import structlog

from os2datascanner.projects.admin.adminapp.utils import capitalize_first

LINK_CHECK_TIMEOUT = 5

logger = structlog.get_logger()


def check_url(url, method="HEAD"):
    """Check a URL using the specified method (GET, or HEAD).

    Return None if the URL can be reached with no errors.
    If the URL can't be checked with HEAD (default), tries a GET request.
    Otherwise, return a dict containing a status_code and status_message
    containing the error information.
    :param url:
    :param method:
    :return:
    """
    try:
        logger.info("check_url", url=url)
        request = urllib.request.Request(url, headers={"User-Agent":
                                                       "OS2Webscanner"})
        request.get_method = lambda: method
        urllib.request.urlopen(request, timeout=LINK_CHECK_TIMEOUT)
        return None
    except (urllib.error.HTTPError,
            urllib.error.URLError,
            http.client.InvalidURL,
            socket.timeout,
            IOError, ssl.CertificateError) as e:
        logger.exception("check_url")
        code = getattr(e, "code", 0)
        if code == 405:
            # Method not allowed, try with GET instead
            result = check_url(url, method="GET")
            return result

        reason = str(getattr(e, "reason", ""))
        if not reason:
            reason = str(e)

        # Strip [Errno: -2] stuff
        reason = regex.sub("\[.+\] ", "", reason)
        reason = capitalize_first(reason)

        if code:
            reason = "%d %s" % (code, reason)

        return {"status_code": code, "status_message": reason}
