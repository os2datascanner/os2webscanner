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
