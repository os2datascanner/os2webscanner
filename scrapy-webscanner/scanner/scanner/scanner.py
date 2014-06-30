import mimetypes

from scrapy import log
from twisted.internet import defer

from ..rules.name import NameRule
from ..rules.cpr import CPRRule
from ..rules.regexrule import RegexRule

from ..processors import html, pdf
from ..processors.processor import ProcessRequest
from django.utils import timezone
from os2webscanner.models import Scan, Domain

class Scanner:
    processors = {
        'application/pdf': pdf.PDFProcessor,
        'text/html': html.HTMLProcessor,
        }

    def __init__(self, scan_id):
        """Initialize the Scanner with the given scan_id to be loaded from the
        database."""
        # Get scan object from DB
        self.scan_object = Scan.objects.get(pk=scan_id)

        # Update start_time to now and status to STARTED
        self.scan_object.start_time = timezone.now()
        self.scan_object.status = Scan.STARTED
        self.scan_object.save()
        self.scanner_object = self.scan_object.scanner
        self.rules = self.load_rules()

        self.valid_domains = self.scanner_object.domains.filter(validation_status=Domain.VALID)

        self.init_processors()

    def init_processors(self):
        """Initialize each Processor object with a reference to the Scanner"""
        self.deferred_count = 0
        for mime in self.processors.keys():
            self.processors[mime] = self.processors[mime](scanner=self)

    def load_rules(self):
        """Load rules based on Scanner settings."""
        rules = []
        if self.scanner_object.do_cpr_scan:
            rules.append(CPRRule())
        if self.scanner_object.do_name_scan:
            rules.append(NameRule(whitelist=self.scanner_object.whitelisted_names))
        # TODO: Add Regex Rules
        for rule in self.scanner_object.regex_rules.all():
            rules.append(RegexRule(name=rule.name, match_string=rule.match_string, sensitivity=rule.sensitivity))
        return rules

    def get_sitemap_urls(self):
        """Returns a list of sitemap.xml URLs including any uploaded sitemap.xml file."""
        urls = []
        for domain in self.valid_domains:
            # TODO: Do some normalization of the URL to get the sitemap.xml file
            root_url = domain.url
            if not root_url.startswith('http://') and not root_url.startswith('https://'):
                root_url = 'http://%s/' % root_url
            urls.append(root_url + "/sitemap.xml")
            # Add uploaded sitemap.xml file
            if domain.sitemap != '':
                from django.conf import settings
                sitemap_path = "%s/%s" % (settings.BASE_DIR, domain.sitemap.url)
                urls.append('file://' + sitemap_path)
        return urls

    def get_domains(self):
        """Returns a list of domain URLs."""
        return [d.url for d in self.valid_domains]

    def scan(self, data, matches_callback, url="", mime_type=None):
        """Scans data for matches executing all the rules
        associated with this scanner."""
        self.process(data, url=url, mime_type=mime_type,
                     processed_callback = lambda result: self.processed(result, matches_callback))

    def processed(self, result, matches_callback):
        if isinstance(result, basestring):
            matches = self.execute_rules(result)
            log.msg("Matches: %s" % matches)
            matches_callback(matches)
        else:
            log.msg("processed requests %s" % result)
            for r in result:
                if isinstance(r, ProcessRequest):
                    # Recursively process any returned ProcessRequests
                    self.process(r.data, processed_callback = lambda result: self.processed(result, matches_callback), url=r.url, mime_type=r.mime_type)
                else:
                    matches = self.execute_rules(r)
                    matches_callback(matches)


    def process(self, data, processed_callback, url="", mime_type=None):
        """Processes the data, returning text or Deferred if it was set aside to process in the background."""
        if not mime_type and url != "":
            log.msg("Guessing mime-type based on file extension", level=log.DEBUG)
            mime_type, encoding = mimetypes.guess_type(url)

        if mime_type is None:
            # Default to process as plain text
            mime_type = 'text/plain'

        log.msg("Scanning " + url + " Mime-type: " + mime_type)

        processor = self.processors.get(mime_type, None)
        if processor is not None:
            if callable(processor.process):
                log.msg("Processing with " + processor.__class__.__name__)
                # Process the text (for example to remove HTML, or add to conversion queue)
                processor.process(data, processed_callback)
            else:
                raise Exception("Processor lacks process method")
        else:
            log.msg("No processor available for mime type: " + mime_type)

    def active_processor_count(self):
        return self.deferred_count

    def is_processing(self):
        return self.deferred_count > 0

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
