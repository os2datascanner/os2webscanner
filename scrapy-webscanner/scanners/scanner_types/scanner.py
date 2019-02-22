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

"""Contains a WebScanner."""
import logging

from ..rules.name import NameRule
from ..rules.address import AddressRule
from ..rules.regexrule import RegexRule
from ..rules.cpr import CPRRule

from ..processors.processor import Processor


class Scanner(object):
    """Represents a scanner which can scan data using configured rules."""

    def __init__(self, scan_id):
        """Load the scanner settings from the given scan ID."""
        # Get scan object from DB
        from os2webscanner.models.scans.scan_model import Scan
        self.scan_object = Scan.objects.get(pk=scan_id)

        self.rules = self._load_rules()
        self.valid_domains = self.scan_object.get_valid_domains

    def _load_rules(self):
        """Load rules based on WebScanner settings."""
        rules = []
        if self.scan_object.do_name_scan:
            rules.append(
                NameRule(whitelist=self.scan_object.whitelisted_names,
                         blacklist=self.scan_object.blacklisted_names)
            )
        if self.scan_object.do_address_scan:
            rules.append(
                AddressRule(whitelist=self.scan_object.whitelisted_addresses,
                            blacklist=self.scan_object.blacklisted_addresses)
            )
        # Add Regex Rules
        for rule in self.scan_object.regex_rules.all():
            rules.append(
                RegexRule(
                    name=rule.name,
                    pattern_strings=rule.patterns.all(),
                    sensitivity=rule.sensitivity,
                    cpr_enabled=rule.cpr_enabled,
                    ignore_irrelevant=rule.ignore_irrelevant,
                    do_modulus11=rule.do_modulus11
                )
            )
        return rules

    def get_exclusion_rules(self):
        """Return a list of exclusion rules associated with the WebScanner."""
        exclusion_rules = []
        for domain in self.valid_domains:
            exclusion_rules.extend(domain.exclusion_rule_list())
        return exclusion_rules

    def get_sitemap_urls(self):
        """Return a list of sitemap.xml URLs across all the scanner's domains.
        """
        urls = []
        for domain in self.valid_domains:
            # Do some normalization of the URL to get the sitemap.xml file
            sitemap_url = domain.webdomain.get_sitemap_url()
            if sitemap_url:
                urls.append(sitemap_url)
        return urls

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
            logging.info("{} is handled by processor of type {}".format(
                url_object.url, processor_type))
            return processor.handle_spider_item(data, url_object)

    def execute_rules(self, text):
        """Execute the scanner's rules on the given text.

        Returns a list of matches.
        """
        matches = []
        for rule in self.rules:
            print('-------Rule to be executed {0}-------'.format(rule))
            rule_matches = rule.execute(text)

            if isinstance(rule, CPRRule):
                for match in rule_matches:
                    match['matched_rule'] = rule.name
                    matches.extend(rule_matches)
            else:
                #skip a ruleset where not all the rules match
                if not rule.is_all_match(rule_matches):
                    continue

                # Associate the rule with the match
                print('-------Rule matches length {0}-------'.format(str(len(rule_matches))))

                match = rule_matches.pop()
                match['matched_rule'] = rule.name
                for item in rule_matches:
                    match['matched_data'] += ', ' + item['matched_data']

                print('-------Match: {0}-------'.format(match))

                matches.append(match)
        return matches
