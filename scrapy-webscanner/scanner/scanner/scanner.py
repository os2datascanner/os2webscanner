import re
import mimetypes
from datetime import datetime

from scrapy import log

from ..rules.name import NameRule
from ..rules.cpr import CPRRule
from ..rules.regexrule import RegexRule
from ..items import UrlItem, ScanItem

from ..processors import html
from os2webscanner.models import Scan, Url


class Scanner:
    processors = {
        # 'application/pdf': pdf2html,
        'text/html': html.HTMLProcessor(),
        }

    def __init__(self, scan_id):
        """Initialize the Scanner with the given scan_id to be loaded from the
        database."""
        # Get scan object from DB
        self.scan_object = Scan.objects.get(pk=scan_id)

        # Update start_time to now and status to STARTED
        self.scan_object.start_time = datetime.now()
        self.scan_object.status = Scan.STARTED
        self.scan_object.save()
        self.scanner_object = self.scan_object.scanner
        self.rules = self.load_rules()

    def load_rules(self):
        """Load rules based on Scanner settings."""
        rules = []
        if self.scanner_object.do_cpr_scan:
            rules.append(CPRRule())
        if self.scanner_object.do_name_scan:
            rules.append(NameRule())
        # TODO: Add Regex Rules
        for rule in self.scanner_object.regex_rules.all():
            rules.append(RegexRule(name=rule.name, match_string=rule.match_string, sensitivity=rule.sensitivity))
        return rules

    def get_sitemap_urls(self):
        """Returns a list of sitemap.xml URLs including any uploaded sitemap.xml file."""
        urls = []
        for domain in self.scanner_object.domains.all():
            # TODO: Do some normalization of the URL to get the sitemap.xml file
            root_url = domain.url
            if not root_url.startswith('http://') and not root_url.startswith('https://'):
                root_url = 'http://%s/' % root_url
            urls.append(root_url + "/sitemap.xml")
            urls.append(root_url + "/sitemap.xml.gz")
            # Add uploaded sitemap.xml file
            if domain.sitemap != '':
                urls.append('file://' + domain.sitemap)
        return urls

    def get_domains(self):
        """Returns a list of domain URLs."""
        return [d.url for d in self.scanner_object.domains.all()]

    def scan(self, response):
        """Scans a scrapy Response object for matches executing all the rules
        associated with this scanner."""
        # Get the mime-type from the Content-Type header or the file extension
        content_type = response.headers.get('content-type')
        if content_type:
            mime_type = parse_content_type(content_type)
            log.msg("Content-Type: " + content_type, level=log.DEBUG)
        else:
            log.msg("Guessing mime-type based on file extension", level=log.DEBUG)
            mime_type = mimetypes.guess_type(response.url)
            if mime_type is None:
                mime_type = 'text/plain'

        log.msg("Scanning " + response.url + " Mime-type: " + mime_type)

        # Save the URL item to the database
        url_object = Url(url=response.url, mime_type=mime_type, scan=self.scan_object)
        url_object.save()

        processor = self.processors.get(mime_type, None)
        matches = []
        if processor is not None:
            if callable(processor.process):
                log.msg("Processing with " + processor.__class__.__name__)
                # Process the text (for example to remove HTML, or add to conversion queue)
                text = processor.process(response)
                # TODO: Check if the processor only adds it to the conversion queue
                matches = self.execute_rules(text)
            else:
                raise Exception("Processor lacks process method")
        else:
            log.msg("No processor available for mime type: " + mime_type)
        for match in matches:
            match['url'] = url_object
            match['scan'] = self.scan_object
        return matches

    def execute_rules(self, text):
        """Executes the scanner's rules on the given text returning a list of matches"""
        matches = []
        for rule in self.rules:
            rule_matches = rule.execute(text)
            # TODO: Associate the URL and scan with each match
            for match in rule_matches:
                match['matched_rule'] = rule.name
            matches.extend(rule_matches)
        return matches

def parse_content_type(content_type):
    """Parses and returns the mime-type from a Content-Type header value"""
    m = re.search('([^/]+/[^;\s]+)', content_type)
    return m.group(1)
