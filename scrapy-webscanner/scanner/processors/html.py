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

from processor import Processor
from w3lib.html import remove_tags, replace_entities

from text import TextProcessor
from scrapy import log
import os


class HTMLProcessor(Processor):

    """Processor for HTML, XML and SGML documents.

    When processing, replaces entities and removes tags (except comments).
    Immediately processes with TextProcessor after processing.
    """

    item_type = "html"
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
        """Process HTML data.

        Replaces entities and removes tags (except comments) before
        processing with TextProcessor.
        """
        log.msg("Process HTML %s" % url_object.url)
        # Convert HTML entities to their unicode representation
        entity_replaced_html = replace_entities(data)
        # Strip tags from the HTML (except comments)
        no_tags_html = remove_tags(entity_replaced_html, keep=("!--",))
        return self.text_processor.process(no_tags_html, url_object)


Processor.register_processor(HTMLProcessor.item_type, HTMLProcessor)
