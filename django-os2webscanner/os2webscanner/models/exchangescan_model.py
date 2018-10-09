from django.db import models
from .scan_model import Scan


class ExchangeScan(Scan):
    """An actual instance of the exchange scanning process done by a exchange scanner."""
    def __init__(self, *args, **kwargs):
        """Initialize a new scan.

        Stores the old status of the scan for later use.
        """
        super().__init__(*args, **kwargs)
        self._old_status = self.status

# Create method - copies fields from scanner
    @classmethod
    def create(scan_cls, scanner):
        """ Create and copy fields from scanner. """
        scan = scan_cls(
            is_visible=scanner.is_visible,
            whitelisted_names=scanner.organization.name_whitelist,
            blacklisted_names=scanner.organization.name_blacklist,
            whitelisted_addresses=scanner.organization.address_whitelist,
            blacklisted_addresses=scanner.organization.address_blacklist,
            whitelisted_cprs=scanner.organization.cpr_whitelist,
            do_name_scan=scanner.do_name_scan,
            do_address_scan=scanner.do_address_scan,
            do_ocr=scanner.do_ocr,
            columns=scanner.columns,
            output_spreadsheet_file=scanner.output_spreadsheet_file,
            do_cpr_replace=scanner.do_cpr_replace,
            cpr_replace_text=scanner.cpr_replace_text,
            do_name_replace=scanner.do_name_replace,
            name_replace_text=scanner.name_replace_text,
            do_address_replace=scanner.do_address_replace,
            address_replace_text=scanner.address_replace_text,
        )
        #
        scanner.is_running = True
        scanner.save()
        scan.status = Scan.NEW
        scan.scanner = scanner
        scan.save()
        scan.domains.add(*scanner.domains.all())
        scan.regex_rules.add(*scanner.regex_rules.all())
        scan.recipients.add(*scanner.recipients.all())

        return scan

    class Meta:
        db_table = 'os2webscanner_exchangescan'
