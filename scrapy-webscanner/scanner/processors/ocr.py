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
"""OCR Processors."""


import os
import subprocess

from scrapy import log

from processor import Processor
from text import TextProcessor


class OCRProcessor(Processor):

    """A processor which uses tesseract OCR to process an image."""

    item_type = "ocr"
    text_processor = TextProcessor()

    def handle_spider_item(self, data, url_object):
        """Add the item to the queue."""
        return self.add_to_queue(data, url_object)

    def handle_queue_item(self, item):
        """Convert the queue item."""
        return self.convert_queue_item(item)

    def convert(self, item, tmp_dir):
        """Convert the item and immediately run a Text processor on it."""
        txt_file = os.path.join(tmp_dir, "file")
        return_code = subprocess.call([
            "tesseract", item.file_path, txt_file,
            "-psm", "1", "-l", "dan+eng"
        ])
        if return_code != 0:
            return False

        txt_file += ".txt"
        log.msg("Processing file {0}".format(txt_file))
        self.text_processor.process_file(txt_file, item.url, item.page_no)
        if os.path.exists(txt_file):
            os.remove(txt_file)
        return return_code == 0


Processor.register_processor(OCRProcessor.item_type, OCRProcessor)
