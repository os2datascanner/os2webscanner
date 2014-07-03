import re
import urllib2
import urlparse
from os2webscanner.models import Domain


def _do_request(url):
    try:
        request = urllib2.Request(url, headers={"User-Agent": "OS2Webscanner"})
        r = urllib2.urlopen(request)
        return r.read()
    except urllib2.URLError, urllib2.HTTPError:
        return None


def validate_domain(domain):
    """Validate a Domain by using the validation method specified
    by the Domain object. Returns True if it validated or False if it did
    not."""
    validators = {
        Domain.ROBOTSTXT: {
            "url": "/robots.txt",
            "regex": "User-agent: OS2Webscanner(\r\n|\r|\n)Disallow:"
        },
        Domain.WEBSCANFILE: {
            "url": "/webscan.html",
            "regex": "OS2Webscanner"
        },
        Domain.METAFIELD: {
            "url": "/",
            "regex": '<meta name="os2webscanner" content="allowed"'
        }
    }
    validator = validators[domain.validation_method]
    url = urlparse.urljoin(domain.root_url, validator["url"])
    r = _do_request(url)
    if r is None:
        return False
    match = re.search(validator["regex"], r, re.I)
    return match is not None
