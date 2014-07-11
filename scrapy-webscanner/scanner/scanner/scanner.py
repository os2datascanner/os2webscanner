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
"""Contains a Scanner."""
from urlparse import urljoin, urlparse

from ..rules.name import NameRule
from ..rules.cpr import CPRRule
from ..rules.regexrule import RegexRule

from ..processors.processor import Processor
from os2webscanner.models import Scan, Domain


class Scanner:
    """Represents a scanner which can scan data using configured rules."""

    def __init__(self, scan_id):
        """Load the scanner settings from the given scan ID."""
        # Get scan object from DB
        self.scan_object = Scan.objects.get(pk=scan_id)
        self.scanner_object = self.scan_object.scanner
        self.rules = self._load_rules()
        self.valid_domains = self.scanner_object.domains.filter(
            validation_status=Domain.VALID
        )

    def _load_rules(self):
        """Load rules based on Scanner settings."""
        rules = []
        if self.scanner_object.do_cpr_scan:
            rules.append(CPRRule())
        if self.scanner_object.do_name_scan:
            rules.append(
                NameRule(whitelist=self.scanner_object.whitelisted_names)
            )
        # Add Regex Rules
        for rule in self.scanner_object.regex_rules.all():
            rules.append(
                RegexRule(
                    name=rule.name,
                    match_string=rule.match_string,
                    sensitivity=rule.sensitivity
                )
            )
        return rules

    def get_exclusion_rules(self):
        """Return a list of exclusion rules associated with the Scanner."""
        exclusion_rules = []
        for domain in self.valid_domains:
            exclusion_rules.extend(domain.exclusion_rule_list())
        return exclusion_rules

    def get_sitemap_urls(self):
        """Return a list of sitemap.xml URLs.

        This includes any uploaded sitemap.xml file.
        """
        urls = []
        for domain in self.valid_domains:
            # Do some normalization of the URL to get the sitemap.xml file
            urls.append(urljoin(domain.root_url, "/sitemap.xml"))
            # Add uploaded sitemap.xml file
            if domain.sitemap != '':
                urls.append('file://' + domain.sitemap_full_path)
        return urls

    def get_domains(self):
        """Return a list of domains."""
        domains = []
        for d in self.valid_domains:
            if d.url.startswith('http://') or d.url.startswith('https://'):
                domains.append(urlparse(d.url).hostname)
            else:
                domains.append(d.url)
        return domains

    def scan(self, data, url_object):
        """Scan data for matches from a spider.

        Processes the data using the appropriate processor for the mime-type
        of the url_object parameter. The processor will either handle the data
        immediately or add it to a conversion queue.
        Returns True if the data was processed successfully or if the item
        was queued to be processed.
        """
        processor_type = Processor.mimetype_to_processor_type(
            url_object.mime_type
        )
        processor = Processor.processor_by_type(processor_type)
        if processor is not None:
            return processor.handle_spider_item(data, url_object)

    def execute_rules(self, text):
        """Execute the scanner's rules on the given text.

        Returns a list of matches.
        """
        matches = []
        for rule in self.rules:
            rule_matches = rule.execute(text)
            # Associate the rule with the match
            for match in rule_matches:
                match['matched_rule'] = rule.name
            matches.extend(rule_matches)
        return matches
