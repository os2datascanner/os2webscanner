from urllib.parse import urlparse

from os2datascanner.projects.admin.adminapp.models.scans.webscan_model import WebScan
from os2datascanner.projects.admin.adminapp.models.webversion_model import WebVersion

from ...utils import as_file_uri
from .scanner import Scanner


class WebScanner(Scanner):

    version_class = WebVersion
    scan_class = WebScan

    @property
    def do_link_check(self):
        return self.scan_object.do_link_check

    @property
    def do_external_link_check(self):
        return self.scan_object.do_external_link_check

    @property
    def do_last_modified_check_head_request(self):
        return self.scan_object.do_last_modified_check_head_request

    def get_domain_url(self):
        """Return a list of valid domain urls."""
        scanner = self.get_scanner_object()

        if scanner.url.startswith('http://') or scanner.url.startswith('https://'):
            return urlparse(scanner.url).hostname
        else:
            return scanner.url

    def get_sitemap_urls(self):
        """Return a list of sitemap.xml URLs across all the scanner's domains.
        """
        # Do some normalization of the URL to get the sitemap.xml file
        sitemap_url = self.scan_object.webscanner.get_sitemap_url()

        return [sitemap_url] if sitemap_url else []

    def get_uploaded_sitemap_urls(self):
        """Return a list of uploaded sitemap.xml files for all scanner domains.
        """
        if self.scan_object.webscanner.sitemap:
            return [as_file_uri(self.scan_object.webscanner.sitemap_full_path)]
        return []
