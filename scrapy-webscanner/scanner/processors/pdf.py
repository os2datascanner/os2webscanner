from scrapy import log

from processor import Processor
from w3lib.html import remove_tags, replace_entities

import tempfile
from subprocess import Popen
import shutil
import os

import contextlib

@contextlib.contextmanager
def temporary_directory(*args, **kwargs):
    d = tempfile.mkdtemp(*args, **kwargs)
    try:
        yield d
    finally:
        shutil.rmtree(d)

class PDFProcessor(Processor):
    def process(self, data):
        print "Process PDF"
        text = ""

        # Create a temporary directory for the conversion
        with temporary_directory() as temp_dir:
            # Write the temporary file to the temporary directory
            temp_file, temp_file_path = tempfile.mkstemp(dir=temp_dir)
            os.write(temp_file, data)
            os.close(temp_file)

            # Run the conversion and wait for it to finish
            process = Popen(["pdftohtml", "-noframes", "-hidden", temp_file_path])
            process.wait()

            # Remove the temporary file so we don't reprocess it
            os.remove(temp_file_path)

            # Process all files in the temporary directory
            # TODO: Recursively?
            files = [os.path.join(temp_dir, file) for file in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, file))]

            # TODO: Should we really just queue these files for scanning instead of scanning directly?
            for file in files:
                # Scan each file
                try:
                    log.msg("Opening file %s" % file)
                    f = open(file, "r")
                    text += self.scanner.process(f.read(), url=file) + "\n"
                except IOError, e:
                    log.msg("Error reading converted file %s: %s" % (file, repr(e)), level=log.ERROR)
                else:
                    f.close()

        return text