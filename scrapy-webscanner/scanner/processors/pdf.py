from processor import Processor
import shutil
import os
import subprocess

class PDFProcessor(Processor):
    item_type = "pdf"

    def handle_spider_item(self, data, url_object):
        return self.add_to_queue(data, url_object)

    def handle_queue_item(self, item):
        return self.convert_queue_item(item)

    def convert(self, item, tmp_dir):
        # Move file to temp dir before conversion
        shutil.move(item.file_path, tmp_dir)
        new_file_path = os.path.join(tmp_dir, os.path.basename(item.file_path))
        return_code = subprocess.call(["pdftohtml", "-noframes", "-hidden", "-q", new_file_path])
        os.remove(new_file_path)
        return return_code == 0

Processor.register_processor(PDFProcessor.item_type, PDFProcessor)