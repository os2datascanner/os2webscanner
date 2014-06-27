from twisted.internet import threads
from scrapy import log

from processor import Processor, ProcessRequest

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

class DeferredProcessor(Processor):
    def result_callback(self, results, processed_callback):
        print "Result callback", results
        self.scanner.deferred_count -= 1
        processed_callback(results)

    def process(self, data, callback):
        self.scanner.deferred_count += 1
        d = threads.deferToThread(self.process_func, data)
        d.addCallback(self.result_callback, callback)
        return d

    def command(self, temp_file_path):
        """Returns the command as a list of arguments that will be passed to Popen"""
        raise NotImplemented

    def process_func(self, data):
        print "Process Deferred"
        results = []

        # Create a temporary directory for the conversion
        with temporary_directory() as temp_dir:
            # Write the temporary file to the temporary directory
            temp_file, temp_file_path = tempfile.mkstemp(dir=temp_dir)
            os.write(temp_file, data)
            os.close(temp_file)

            # Run the conversion and wait for it to finish
            process = Popen(self.command(temp_file_path))
            process.wait()

            # Remove the temporary file so we don't reprocess it
            os.remove(temp_file_path)

            # Process all files in the temporary directory
            # TODO: Recursively?
            files = [os.path.join(temp_dir, file) for file in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, file))]

            for file in files:
                # Scan each file
                try:
                    log.msg("Opening file %s" % file)
                    f = open(file, "r")
                    results.append(ProcessRequest(f.read(), url=file))
                except IOError, e:
                    log.msg("Error reading converted file %s: %s" % (file, repr(e)), level=log.ERROR)
                else:
                    f.close()

        return results