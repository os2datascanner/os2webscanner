from ..models.webscanner_model import WebScanner
from .scanner_views import *


class WebScannerList(ScannerList):
    """Displays list of web scanners."""

    model = WebScanner
    type = 'web'


class WebScannerCreate(ScannerCreate):
    """Web scanner create form."""

    model = WebScanner
    fields = ['name', 'schedule', 'domains',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_cpr_ignore_irrelevant',
              'do_name_scan', 'do_ocr', 'do_address_scan',
              'do_link_check', 'do_external_link_check', 'do_collect_cookies',
              'do_last_modified_check', 'do_last_modified_check_head_request',
              'regex_rules', 'recipients']

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/webscanners/%s/created/' % self.object.pk


class WebScannerUpdate(ScannerUpdate):
    """Update a scanner view."""

    model = WebScanner
    fields = ['name', 'schedule', 'domains',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_cpr_ignore_irrelevant',
              'do_name_scan', 'do_ocr', 'do_address_scan',
              'do_link_check', 'do_external_link_check', 'do_collect_cookies',
              'do_last_modified_check', 'do_last_modified_check_head_request',
              'regex_rules', 'recipients']

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/webscanners/%s/saved/' % self.object.pk


class WebScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = WebScanner
    fields = []
    success_url = '/webscanners/'


class WebScannerAskRun(ScannerAskRun):
    """Prompt for starting web scan, validate first."""

    model = WebScanner
