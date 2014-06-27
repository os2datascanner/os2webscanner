from deferred import DeferredProcessor

class PDFProcessor(DeferredProcessor):
    def command(self, temp_file_path):
        return ["pdftohtml", "-noframes", "-hidden", "-q", temp_file_path]