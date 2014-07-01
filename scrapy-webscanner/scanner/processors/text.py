from ..scanner.scanner import Scanner
from processor import Processor

class TextProcessor(Processor):
    item_type = "text"

    def handle_spider_item(self, data, url_object):
        return self.process(data, url_object)

    def handle_queue_item(self, item):
        return self.process_file(item.file_path, item.url)

    def process(self, data, url_object):
        # Execute rules and save matches
        scanner = Scanner(url_object.scan.pk)
        matches = scanner.execute_rules(data)
        for match in matches:
            match['url'] = url_object
            match['scan'] = url_object.scan
            match.save()
        return True

Processor.register_processor(TextProcessor.item_type, TextProcessor)