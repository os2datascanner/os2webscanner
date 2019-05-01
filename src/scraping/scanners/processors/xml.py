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
"""HTML Processors."""

from .processor import Processor

from .text import TextProcessor
import logging
import os

import xmltodict
import json

from xml.parsers.expat import ExpatError
from .html import HTMLProcessor

class XmlProcessor(HTMLProcessor):

    """Processor for XMLdocuments.

    When processing, converts document to json one line including all attributes
    Immediately processes with TextProcessor after processing.
    """

    item_type = "xml"
    text_processor = TextProcessor()

    def handle_spider_item(self, data, url_object):
        """Immediately process the spider item."""
        return self.process(data, url_object)

    def handle_queue_item(self, item):
        """Immediately process the queue item."""
        result = self.process_file(item.file_path, item.url)
        if os.path.exists(item.file_path):
            os.remove(item.file_path)
        return result


    def process(self, data, url_object):
        """Process XML data.

        Converts document to json before processing with TextProcessor.
        if XML is not well formed, treat it as HTML
        """
        logging.info("Process XML %s" % url_object.url)

        try:
            data = json.dumps(xmltodict.parse(data))
            return self.text_processor.process(data, url_object)
        except ExpatError:
            return super(XmlProcessor,self).process(data,url_object)


Processor.register_processor(XmlProcessor.item_type, XmlProcessor)
