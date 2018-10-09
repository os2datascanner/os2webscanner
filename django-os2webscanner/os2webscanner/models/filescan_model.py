# -*- coding: UTF-8 -*-
# encoding: utf-8
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )

from .scan_model import Scan


class FileScan(Scan):

    def __init__(self, *args, **kwargs):
        """Initialize a new scan.

        Stores the old status of the scan for later use.
        """
        super().__init__(*args, **kwargs)
        self._old_status = self.status

    def cleanup_finished_scan(self, log=False):
        """Delete pending conversion queue items and remove the scan dir."""
        if self.is_scan_dir_writable():
            self.delete_scan_dir(log)

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
            do_last_modified_check=scanner.do_last_modified_check,
            columns=scanner.columns,
            output_spreadsheet_file=scanner.output_spreadsheet_file,
            do_cpr_replace=scanner.do_cpr_replace,
            cpr_replace_text=scanner.cpr_replace_text,
            do_name_replace=scanner.do_name_replace,
            name_replace_text=scanner.name_replace_text,
            do_address_replace=scanner.do_address_replace,
            address_replace_text=scanner.address_replace_text
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
        db_table = 'os2webscanner_filescan'
