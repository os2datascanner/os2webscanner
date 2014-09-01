import socket
import urllib2
import regex
from scrapy import log

LINK_CHECK_TIMEOUT = 5


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
        log.msg("Checking %s" % url)
        request = urllib2.Request(url, headers={"User-Agent":
                                                    "OS2Webscanner"})
        request.get_method = lambda: method
        r = urllib2.urlopen(request,
                            timeout=LINK_CHECK_TIMEOUT)
        return None
    except (urllib2.HTTPError, urllib2.URLError, socket.timeout) as e:
        log.msg("Error %s" % e, level=log.DEBUG)
        code = getattr(e, "code", 0)
        if code == 405:
            # Method not allowed, try with GET instead
            result = check_url(url, method="GET")
            return result

        reason = getattr(e, "reason", "")

        # Strip [Errno: -2] stuff at beginning of URLError reason
        reason = regex.sub("^\[.+\]", "", unicode(reason))

        if code != 0:
            reason = "%d %s" % (code, reason)

        return {"status_code": code, "status_message": reason}