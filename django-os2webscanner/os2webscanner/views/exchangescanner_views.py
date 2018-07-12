from .scanner_views import *
from ..models.exchangescanner_model import ExchangeScanner


class ExchangeScannerList(ScannerList):
    """Displays list of exchange scanners."""

    model = ExchangeScanner
    type = 'exchange'


class ExchangeScannerCreate(ScannerCreate):
    """Create a exchange scanner view."""

    model = ExchangeScanner
    fields = ['name', 'schedule', 'domains',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_cpr_ignore_irrelevant',
              'do_name_scan', 'do_ocr', 'do_address_scan', 'do_last_modified_check',
              'regex_rules', 'recipients']

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/exchangescanners/%s/created/' % self.object.pk


class ExchangeScannerUpdate(ScannerUpdate):
    """Update a scanner view."""

    model = ExchangeScanner
    fields = ['name', 'schedule', 'domains',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_cpr_ignore_irrelevant',
              'do_name_scan', 'do_ocr', 'do_address_scan', 'do_last_modified_check',
              'regex_rules', 'recipients']

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/exchangescanners/%s/saved/' % self.object.pk


class ExchangeScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = ExchangeScanner
    fields = []
    success_url = '/exchangescanners/'


class ExchangeScannerAskRun(ScannerAskRun):
    """Prompt for starting exchange scan, validate first."""

    model = ExchangeScanner


class ExchangeScannerRun(ScannerRun):
    """View that handles starting of a exchange scanner run."""

    model = ExchangeScanner
