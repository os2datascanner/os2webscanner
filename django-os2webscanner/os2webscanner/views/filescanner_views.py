from .scanner_views import *
from ..models.filescanner_model import FileScanner

class FileScannerList(ScannerList):
    """Displays list of file scanners."""

    model = FileScanner
    type = 'file'


class FileScannerCreate(ScannerCreate):
    """Create a file scanner view."""

    model = FileScanner
    fields = ['name', 'schedule', 'domains',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_cpr_ignore_irrelevant',
              'do_name_scan', 'do_ocr', 'do_address_scan', 'do_last_modified_check',
              'regex_rules', 'recipients']

    def get_success_url(self):
        """The URL to redirect to after successful creation."""
        return '/filescanners/%s/created/' % self.object.pk


class FileScannerUpdate(ScannerUpdate):
    """Update a scanner view."""

    model = FileScanner
    fields = ['name', 'schedule', 'domains',
              'do_cpr_scan', 'do_cpr_modulus11', 'do_cpr_ignore_irrelevant',
              'do_name_scan', 'do_ocr', 'do_address_scan', 'do_last_modified_check',
              'regex_rules', 'recipients']

    def get_success_url(self):
        """The URL to redirect to after successful update."""
        return '/filescanners/%s/saved/' % self.object.pk


class FileScannerDelete(ScannerDelete):
    """Delete a scanner view."""
    model = FileScanner
    fields = []
    success_url = '/filescanners/'


class FileScannerAskRun(ScannerAskRun):
    """Prompt for starting file scan, validate first."""

    model = FileScanner


class FileScannerRun(ScannerRun):
    """View that handles starting of a file scanner run."""

    model = FileScanner
