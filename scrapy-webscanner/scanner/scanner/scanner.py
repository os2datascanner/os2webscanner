from ..rules.name import NameRule
from ..rules.cpr import CPRRule
from ..rules.regexrule import RegexRule

from ..processors.processor import Processor
from os2webscanner.models import Scan, Domain

class Scanner:
    def __init__(self, scan_id):
        """Initialize the scanner and load the scanner settings from the given
        scan ID in the database."""
        # Get scan object from DB
        self.scan_object = Scan.objects.get(pk=scan_id)
        self.scanner_object = self.scan_object.scanner
        self.rules = self._load_rules()
        self.valid_domains = self.scanner_object.domains.filter(validation_status=Domain.VALID)

    def _load_rules(self):
        """Load rules based on Scanner settings."""
        rules = []
        if self.scanner_object.do_cpr_scan:
            rules.append(CPRRule())
        if self.scanner_object.do_name_scan:
            rules.append(NameRule(whitelist=self.scanner_object.whitelisted_names))
        # Add Regex Rules
        for rule in self.scanner_object.regex_rules.all():
            rules.append(RegexRule(name=rule.name, match_string=rule.match_string, sensitivity=rule.sensitivity))
        return rules

    def get_sitemap_urls(self):
        """Returns a list of sitemap.xml URLs including any uploaded sitemap.xml file."""
        urls = []
        for domain in self.valid_domains:
            # Do some normalization of the URL to get the sitemap.xml file
            root_url = domain.url
            if not root_url.startswith('http://') and not root_url.startswith('https://'):
                root_url = 'http://%s/' % root_url
            urls.append(root_url + "/sitemap.xml")
            # Add uploaded sitemap.xml file
            if domain.sitemap != '':
                urls.append('file://' + domain.sitemap_full_path)
        return urls

    def get_domains(self):
        """Returns a list of domain URLs."""
        return [d.url for d in self.valid_domains]

    def scan(self, data, url_object):
        """Scans data for matches executing all the rules
        associated with this scanner."""
        type = Processor.mimetype_to_processor_type(url_object.mime_type)
        processor = Processor.processor_by_type(type)
        if processor is not None:
            return processor.handle_spider_item(data, url_object)

    def execute_rules(self, text):
        """Executes the scanner's rules on the given text returning a list of matches"""
        matches = []
        for rule in self.rules:
            rule_matches = rule.execute(text)
            # Associate the rule with the match
            for match in rule_matches:
                match['matched_rule'] = rule.name
            matches.extend(rule_matches)
        return matches
    #
    # def process_matches(self, matches, url_object):
    #     for match in matches:
    #         match['url'] = url_object
    #         match['scan'] = self.scanner.scan_object
    #         log.msg("Match: " + str(match))
    #         match.save()