from processor import Processor
from text import TextProcessor
import os
import subprocess

class OCRProcessor(Processor):
    item_type = "ocr"
    text_processor = TextProcessor()

    def handle_spider_item(self, data, url_object):
        return self.add_to_queue(data, url_object)

    def handle_queue_item(self, item):
        return self.convert_queue_item(item)

    def convert(self, item, tmp_dir):
        txt_file = os.path.join(tmp_dir, "file")
        return_code = subprocess.call(["tesseract", item.file_path, txt_file, "-l", "dan+eng"])
        txt_file += ".txt"
        self.text_processor.process_file(txt_file, item.url)
        if os.path.exists(txt_file):
            os.remove(txt_file)
        return return_code == 0

Processor.register_processor(OCRProcessor.item_type, OCRProcessor)