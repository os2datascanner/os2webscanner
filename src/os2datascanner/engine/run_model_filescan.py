from time import sleep
import logging
import multiprocessing
from urllib.parse import urljoin

from .run import StartScan

from ..engine2.model.core import SourceManager
from ..engine2.model.file import FilesystemSource
from .scanners.processors.processor import Processor
from .scanners.scanner_types.filescanner import FileScanner


class StartModelFileScan(StartScan, multiprocessing.Process):
    """A scanner application which can be run."""

    def __init__(self, configuration):
        """
        Initialize the scanner application.
        Takes the JSON descriptor of this scan as its argument.
        """

        super().__init__(configuration)
        multiprocessing.Process.__init__(self)

    def run(self):
        """Updates the scan status and sets the pid.
        Run the scanner, blocking until finished."""
        super().run()

        self.scanner = FileScanner(self.configuration)
        self.scanner.ensure_started()
        try:
            with SourceManager() as sm:
                for domain in self.scanner.valid_domains:
                    domain = domain.filedomain

                    interesting = []

                    all_size = 0
                    all_count = 0

                    interesting_size = 0
                    interesting_count = 0

                    logging.info("Exploring source...")
                    source = FilesystemSource(domain.mountpath)
                    for h in source.handles(sm):
                        mime = h.guess_type()
                        stat = h.follow(sm).get_stat()
                        all_size += stat.st_size
                        all_count += 1
                        if Processor.mimetype_to_processor_type(mime):
                            interesting_size += stat.st_size
                            interesting_count += 1
                            interesting.append(h)
                        if all_count % 1000 == 0:
                            logging.info("Exploring: found {0} files, {1} of which interesting...".format(all_count, interesting_count))
                    logging.info("Exploration complete: found {0} files ({1} bytes), of which {2} ({3} bytes) interesting.".format(all_count, all_size, interesting_count, interesting_size))

                    self.scanner.set_statistics(
                            supported_size=interesting_size,
                            supported_count=interesting_count,
                            relevant_size=all_size,
                            relevant_count=all_count,
                            relevant_unsupported_size=0,
                            relevant_unsupported_count=0)

                    logging.info("Fetching interesting items...")
                    for idx, h in enumerate(interesting):
                        url = urljoin(source.to_url() + "/",
                                str(h.get_relative_path()))
                        url = url.replace(domain.mountpath, domain.url)
                        logging.info("Item {0}/{1}: {2}".format(idx + 1, interesting_count, url))

                        url_object = self.scanner.mint_url(
                                url=url, mime_type=h.guess_type())
                        with h.follow(sm).make_stream() as s:
                            self.scanner.scan(s.read(), url_object)
                    logging.info("Fetched interesting items.")

            logging.info("Waiting for processing to finish...")
            from os2datascanner.sites.admin.adminapp.models.conversionqueueitem_model import ConversionQueueItem
            while True:
                remaining_queue_items = ConversionQueueItem.objects.filter(
                    status__in=[ConversionQueueItem.NEW,
                                ConversionQueueItem.PROCESSING],
                    url__scan=self.scanner.scan_object
                ).count()
                if not remaining_queue_items:
                    break
                else:
                    logging.info("Keeping scan alive: {0} remaining queue items...".format(remaining_queue_items))
                    sleep(60)
        finally:
            logging.info("Processing finished. Scan {0} finished.".format(self.scan_id))
            self.scanner.done()

