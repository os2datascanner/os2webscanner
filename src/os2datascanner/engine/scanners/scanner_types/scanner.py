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

import structlog

from os2datascanner.projects.admin.adminapp.models.scans.scan_model import Scan
from os2datascanner.projects.admin.adminapp.models.webversion_model import WebVersion

from ..rules.name import NameRule
from ..rules.address import AddressRule
from ..rules.regexrule import RegexRule
from ..rules.cpr import CPRRule

from ..processors.processor import Processor

logger = structlog.get_logger()


class Scanner(object):
    """Represents a scanner which can scan data using configured rules."""

    def __init__(self, configuration, _Model=None):
        """\
Loads the scanner settings from the scan ID specified in the configuration \
dictionary."""
        self.configuration = configuration
        scan_id = configuration['id']

        self.logger = logger.bind(scan_id=scan_id)

        # Get scan object from DB
        if not _Model:
            _Model = Scan
        self.scan_object = _Model.objects.get(pk=scan_id)

        self.rules = self._load_rules()
        self.valid_domains = self.scan_object.get_valid_domains

    def ensure_started(self):
        if self.scan_object.status != "STARTED":
            self.scan_object.set_scan_status_start()

    def done(self):
        self.scan_object.set_scan_status_done()

    def failed(self, arg):
        self.scan_object.set_scan_status_failed(arg)

    @property
    def do_name_scan(self):
        return self.scan_object.do_name_scan

    @property
    def do_address_scan(self):
        return self.scan_object.do_address_scan

    @property
    def do_ocr(self):
        return self.scan_object.do_ocr

    @property
    def do_last_modified_check(self):
        return self.scan_object.do_last_modified_check

    @property
    def process_urls(self):
        return self.scan_object.scanner.process_urls

    def mint_url(self, **kwargs):
        u = WebVersion(scan=self.scan_object, **kwargs)
        u.save()
        return u

    @staticmethod
    def from_scan_id(scan_id):
        """\
Creates a new Scanner, the settings of which will be loaded from the given \
scan ID."""
        return Scanner(dict(id=scan_id))

    def _load_rules(self):
        """Load rules based on WebScanner settings."""
        rules = []
        if self.do_name_scan:
            rules.append(
                NameRule(whitelist=self.scan_object.whitelisted_names,
                         blacklist=self.scan_object.blacklisted_names)
            )
        if self.do_address_scan:
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
            self.logger.info(
                "will_scan",
                url=url_object.url,
                processor_type=processor_type,
            )
            return processor.handle_spider_item(data, url_object)
        else:
            self.logger.debug(
                "wont_scan",
                url=url_object.url,
                processor_type=processor_type,
            )

    def execute_rules(self, text):
        """Execute the scanner's rules on the given text.

        Returns a list of matches.
        """
        matches = []
        for rule in self.rules:
            self.logger.info('execute_rule', rule=rule)

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
                self.logger.info('rule_matches', length=len(rule_matches))

                match = rule_matches.pop()
                match['matched_rule'] = rule.name
                for item in rule_matches:
                    match['matched_data'] += ', ' + item['matched_data']

                matches.append(match)
        return matches

    def __enter__(self):
        self.ensure_started()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.done()
        else:
            self.logger.exception("SCANNER FAILED", exc_info=exc_value)
            self.failed('SCANNER FAILED: {}'.format(exc_value))
