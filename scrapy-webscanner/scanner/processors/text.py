"""Text Processors."""

from ..scanner.scanner import Scanner
from processor import Processor
import os


class TextProcessor(Processor):

    """Processes plain text."""

    item_type = "text"

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
        """Process the text, by executing rules and saving matches."""
        scanner = Scanner(url_object.scan.pk)
        matches = scanner.execute_rules(data)
        for match in matches:
            match['url'] = url_object
            match['scan'] = url_object.scan
            match.save()
        return True

Processor.register_processor(TextProcessor.item_type, TextProcessor)
