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
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
"""Contains the base scanner spider."""
import re

from scrapy import Spider
from scrapy.utils.httpobj import urlparse_cached


class BaseScannerSpider(Spider):

    """A base spider which is setup to filter offsite domains/excluded URLs."""

    name = 'scanner'

    def __init__(self, scanner, *a, **kw):
        """Initialize the ScannerSpider with a Scanner object.

        The configuration will be loaded from the Scanner.
        """
        super(BaseScannerSpider, self).__init__(*a, **kw)

        self.scanner = scanner

        self.exclusion_rules = self.scanner.get_exclusion_rules()
        self.allowed_domains = self.scanner.get_domains()

    def is_offsite(self, request):
        """Return whether the request is offsite."""
        regex = self.get_host_regex()
        host = urlparse_cached(request).hostname or ''
        return not bool(regex.search(host))

    def is_excluded(self, request):
        """Return whether the request is excluded (due to exclusion rules)."""
        # Build a string to match against, containing the path, and if
        # present, the query and fragment as well.
        url = urlparse_cached(request)
        match_against = url.netloc + url.path
        if url.query != '':
            match_against += "?" + url.query
        if url.fragment != '':
            match_against += "#" + url.fragment

        for rule in self.exclusion_rules:
            if isinstance(rule, basestring):
                # Do case-insensitive substring search
                if match_against.lower().find(rule.lower()) != -1:
                    return True
            else:
                # Do regex search against the URL
                if rule.search(match_against) is not None:
                    return True
        return False

    def get_host_regex(self):
        """Return a regex for which hosts should be included in the scan."""
        if not self.allowed_domains:
            return re.compile('')  # allow all by default
        domain_regexes = []
        for d in self.allowed_domains:
            if d is not None:
                if d.startswith('*.'):
                    # Allow all subdomains
                    domain_regexes.append('(.*\.)?' + re.escape(d[2:]))
                else:
                    domain_regexes.append(re.escape(d))
        regex = r'^(www\.)?(%s)$' % '|'.join(domain_regexes)
        return re.compile(regex)
