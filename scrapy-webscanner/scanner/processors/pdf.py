from processor import Processor
import shutil
import os
import subprocess
import regex


class PDFProcessor(Processor):
    item_type = "pdf"

    def handle_spider_item(self, data, url_object):
        return self.add_to_queue(data, url_object)

    def handle_queue_item(self, item):
        return self.convert_queue_item(item)

    def convert(self, item, tmp_dir):
        # Move file to temp dir before conversion
        new_file_path = os.path.join(tmp_dir, os.path.basename(item.file_path))
        if item.file_path != new_file_path:
            shutil.move(item.file_path, tmp_dir)
        return_code = subprocess.call([
            "pdftohtml", "-noframes", "-hidden", "-enc", "UTF-8",
            "-q", new_file_path
        ])

        if return_code != 0:
            return False

        # Have to get rid of FEFF marks in the generated files
        result_file = regex.sub("\\.pdf$", ".html", new_file_path)
        if(os.path.exists(result_file)):
            return_code = subprocess.call([
                'sed', '-i', 's/\\xff//;s/\\xfe//', result_file
            ])

        os.remove(new_file_path)
        return return_code == 0

Processor.register_processor(PDFProcessor.item_type, PDFProcessor)
