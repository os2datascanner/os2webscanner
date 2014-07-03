"""Contains a Scanner."""

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
            urls.append(domain.root_url + "/sitemap.xml")
            # Add uploaded sitemap.xml file
            if domain.sitemap != '':
                urls.append('file://' + domain.sitemap_full_path)
        return urls

    def get_domains(self):
        """Return a list of domain URLs."""
        return [d.url for d in self.valid_domains]

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
