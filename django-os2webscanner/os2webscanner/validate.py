import re
import urllib2
import urlparse
import hashlib
from os2webscanner.models import Domain


def _do_request(url):
    try:
        request = urllib2.Request(url, headers={"User-Agent": "OS2Webscanner"})
        r = urllib2.urlopen(request)
        return r.read()
    except urllib2.URLError, urllib2.HTTPError:
        return None


def _get_validation_hash(domain):
    """Return the validation hash for the domain.

    The validation hash is based on the domain's organization's primary key.
    """
    return hashlib.md5(str(domain.organization.pk)).hexdigest()


def get_validation_str(domain, method=None):
    """Return the validation string for the domain.

    The validation string is what must be inserted by the user into a
    specific file in the root of the domain. The validation string returned is
    dependent on the domain's validation method and the domain's
    organization.
    """
    hash_str = _get_validation_hash(domain)
    if method is None:
        method = domain.validation_method
    if method == Domain.ROBOTSTXT:
        return "User-agent: " + hash_str + "\nDisallow:"
    elif method == Domain.WEBSCANFILE:
        return hash_str
    elif method == Domain.METAFIELD:
        return '<meta name="os2webscanner" content="' + hash_str + '" />'


def validate_domain(domain):
    """Validate a Domain by using the validation method specified
    by the Domain object. Returns True if it validated or False if it did
    not."""

    hash_str = _get_validation_hash(domain)

    validators = {
        Domain.ROBOTSTXT: {
            "url": "/robots.txt",
            "regex": "User-agent: " + hash_str + "(\r\n|\r|\n)Disallow:"
        },
        Domain.WEBSCANFILE: {
            "url": "/webscan.html",
            "regex": hash_str
        },
        Domain.METAFIELD: {
            "url": "/",
            "regex": '<meta name="os2webscanner" content="' + hash_str + '"'
        }
    }
    validator = validators[domain.validation_method]
    url = urlparse.urljoin(domain.root_url, validator["url"])
    r = _do_request(url)
    if r is None:
        return False
    match = re.search(validator["regex"], r, re.I)
    return match is not None
