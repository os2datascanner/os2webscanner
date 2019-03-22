from urllib.parse import urlparse

from .scanner import Scanner


class WebScanner(Scanner):

    def __init__(self, configuration):
        """\
Loads the scanner settings from the scan ID specified in the configuration \
dictionary."""
        self.configuration = configuration
        scan_id = configuration['id']

        # Get scan object from DB
        from os2webscanner.models.scans.webscan_model import WebScan
        self.scan_object = WebScan.objects.get(pk=scan_id)

        self.rules = self._load_rules()
        self.valid_domains = self.scan_object.get_valid_domains

    def get_domain_urls(self):
        """Return a list of valid domain urls."""
        domains = []
        for d in self.valid_domains:
            if d.url.startswith('http://') or d.url.startswith('https://'):
                domains.append(urlparse(d.url).hostname)
            else:
                domains.append(d.url)
        return domains

    def get_domain_objects(self):
        """
        Returns a list of valid domain objects
        :return: domain list
        """
        domains = []
        for domain in self.valid_domains:
            domains.append(domain.webdomain)
        return domains

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

    def get_uploaded_sitemap_urls(self):
        """Return a list of uploaded sitemap.xml files for all scanner domains.
        """
        urls = []
        for domain in self.valid_domains:
            if domain.webdomain.sitemap != '':
                urls.append('file://' + domain.webdomain.sitemap_full_path)
        return urls
