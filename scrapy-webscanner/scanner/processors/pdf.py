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
"""PDF Processors."""

from processor import Processor
import shutil
import os
import subprocess
import regex


class PDFProcessor(Processor):

    """Processor for PDF documents using pdftohtml."""

    item_type = "pdf"

    def handle_spider_item(self, data, url_object):
        """Add the item to the queue."""
        return self.add_to_queue(data, url_object)

    def handle_queue_item(self, item):
        """Convert the queue item."""
        return self.convert_queue_item(item)

    def convert(self, item, tmp_dir):
        """Convert the item using pdftohtml."""
        # Move file to temp dir before conversion
        new_file_path = os.path.join(tmp_dir, os.path.basename(item.file_path))
        if item.file_path != new_file_path:
            shutil.move(item.file_path, tmp_dir)

        extra_options = []
        if not item.url.scan.do_ocr:
            # Ignore images in PDFs if no OCR scanning will be done
            extra_options.append("-i")

        command = ["pdftohtml"]
        command.extend(["-noframes", "-hidden", "-enc",
                        "UTF-8", "-q"])
        command.extend(extra_options)
        command.append(new_file_path)
        return_code = subprocess.call(command)

        if return_code != 0:
            return False

        # Have to get rid of FEFF marks in the generated files
        result_file = regex.sub("\\.pdf$", ".html", new_file_path)
        if os.path.exists(result_file):
            return_code = subprocess.call([
                'sed', '-i', 's/\\xff//;s/\\xfe//', result_file
            ])

        os.remove(new_file_path)
        return return_code == 0

Processor.register_processor(PDFProcessor.item_type, PDFProcessor)
