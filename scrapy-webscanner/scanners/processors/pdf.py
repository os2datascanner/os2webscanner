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

import shutil
import os
import regex

from .processor import Processor
from subprocess import Popen, PIPE, DEVNULL, check_call, call, TimeoutExpired


class PDFProcessor(Processor):

    """Processor for PDF documents using pdftohtml."""

    item_type = "pdf"

    def handle_spider_item(self, data, url_object):
        """Add the item to the queue."""
        return self.add_to_queue(data, url_object)

    def handle_queue_item(self, item):
        """Convert the queue item."""
        return super().convert_queue_item(item)

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
        command.extend(["-noframes", "-hidden", "-nodrm", "-enc",
                        "UTF-8"])
        command.extend(extra_options)
        command.append(new_file_path)

        p = Popen(command, stdin=PIPE, stdout=DEVNULL, stderr=PIPE)
        output, err = p.communicate(b"input data that is passed to subprocess' stdin")

        if err:
            print('pdftohtml conversion error: {} \non document {}'.format(err.decode('utf-8'), new_file_path))

        # pdftohtml returns 1 if pdf is not type pdf or if pdf could not be converted.
        if p.returncode:
            return False

        # Have to get rid of FEFF, i.e. the byte order mark, in the
        # generated files
        result_file = regex.sub("\\.pdf$", ".html", new_file_path)
        if os.path.exists(result_file):
            check_call([
                'sed', '-i', 's/\\xff//;s/\\xfe//', result_file
            ])

        os.remove(new_file_path)
        return p.returncode


Processor.register_processor(PDFProcessor.item_type, PDFProcessor)
