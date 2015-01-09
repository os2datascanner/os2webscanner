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
"""CSV Processor."""
import StringIO
from os2webscanner.models import Match, Sensitivity

from ..scanner.scanner import Scanner
from processor import Processor
from text import TextProcessor

import os
import unicodecsv


class CSVProcessor(Processor):

    """Processes CSV files."""

    item_type = "csv"
    text_processor = TextProcessor()

    def handle_spider_item(self, data, url_object):
        """Immediately process the spider item."""
        return self.process(data, url_object)

    def handle_queue_item(self, item):
        """Process the queue item."""
        result = self.process_file(item.file_path, item.url)
        if os.path.exists(item.file_path):
            os.remove(item.file_path)
        return result

    def process(self, data, url_object):
        """Process the CSV, by executing rules and saving matches."""
        scanner = Scanner(url_object.scan.pk)

        # If we don't have to do any annotation/replacement, treat it like a
        # normal text file for efficiency
        if not scanner.scan_object.output_spreadsheet_file:
            return self.text_processor.process(data, url_object)

        # Try to detect the CSV Dialect using the first 1024 characters of
        # the data
        try:
            dialect = unicodecsv.Sniffer().sniff(data[:1024])
        except unicodecsv.Error:
            # Couldn't detect CSV Dialect, processing failed
            scanner.scan_object.log_occurrence("Could not detect CSV "
                                               "dialect. Could not perform "
                                               "annotation/replacement.")
            return False

        # Sniffer.sniff doesn't set escape character or quoting
        dialect.escapechar = '\\'
        dialect.quoting = unicodecsv.QUOTE_ALL

        # Convert unicode dialect properties to str because csv.Reader
        # expects them to be
        dialect.delimiter = str(dialect.delimiter)
        dialect.quotechar = str(dialect.quotechar)
        dialect.doublequote = str(dialect.doublequote)
        dialect.escapechar = str(dialect.escapechar)
        dialect.lineterminator = str(dialect.lineterminator)
        dialect.skipinitialspace = str(dialect.skipinitialspace)

        rows = []

        # Read CSV file
        reader = unicodecsv.reader(StringIO.StringIO(data.encode('utf-8')),
                                   dialect)
        first_row = True
        for row in reader:
            rules_matched_in_row = set()
            for i in range(len(row)):
                # Execute rules on each cell
                matches = scanner.execute_rules(row[i])
                for match in matches:
                    # Save matches
                    match['url'] = url_object
                    match['scan'] = url_object.scan
                    match.save()

                    # Add the matched rule to the set of rules matched in
                    # this row
                    rules_matched_in_row.add(match['matched_rule'])

                    # Only replace HIGH sensitivity matches
                    if not match['sensitivity'] == Sensitivity.HIGH:
                        continue

                    if (scanner.scan_object.do_cpr_replace and
                            match['matched_rule'] == 'cpr'):
                        replacement = scanner.scan_object.cpr_replace_text
                    elif (scanner.scan_object.do_name_replace and 
                          match['matched_rule'] == 'name'):
                        replacement = scanner.scan_object.name_replace_text
                    elif (scanner.scan_object.do_address_replace and
                          match['matched_rule'] == 'address'):
                        replacement = scanner.scan_object.address_replace_text
                    else:
                        replacement = None

                    # Replace matched text with replacement text dependent
                    # on rule matched if replacement is demanded
                    if replacement is not None:
                        # Some rules like CPR rule mask their matched_data,
                        # so the real matched text is in original_matched_data
                        try:
                            search_text = match['original_matched_data']
                        except KeyError:
                            search_text = match['matched_data']
                        row[i] = row[i].replace(search_text, replacement)

            if first_row:
                # Append column header
                row.append("Matches")
                first_row = False
            else:
                # Add annotation cell
                annotation = ", ".join(Match.get_matched_rule_display_name(rule)
                                       for rule in rules_matched_in_row)
                row.append(annotation)
            rows.append(row)

        # Write to output file
        with open(scanner.scan_object.scan_output_file, 'w') as f:
            writer = unicodecsv.writer(f, dialect)
            writer.writerows(rows)
        return True

Processor.register_processor(CSVProcessor.item_type, CSVProcessor)
