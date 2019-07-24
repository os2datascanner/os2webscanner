from time import sleep
import multiprocessing
from urllib.parse import urljoin

from .run import StartScan

from ..engine2.model.core import SourceManager
from ..engine2.model.file import FilesystemSource
from .scanners.processors.processor import Processor
from .scanners.scanner_types.filescanner import FileScanner

import structlog
logger = structlog.get_logger()


class StartModelFileScan(StartScan, multiprocessing.Process):
    """A scanner application which can be run."""

    def __init__(self, configuration):
        """
        Initialize the scanner application.
        Takes the JSON descriptor of this scan as its argument.
        """

        super().__init__(configuration)
        multiprocessing.Process.__init__(self)
        self.logger = logger.bind(**self.configuration)

    def run(self):
        """Updates the scan status and sets the pid.
        Run the scanner, blocking until finished."""
        super().run()

        self.scanner = FileScanner(self.configuration)
        self.scanner.ensure_started()

        mountpath = self.scanner.get_domain_url()
        url = self.scanner.get_scanner_object().url
        try:
            with SourceManager() as sm:
                interesting = []

                all_size = 0
                all_count = 0

                interesting_size = 0
                interesting_count = 0

                self.logger.info("exploring_source")
                source = FilesystemSource(mountpath)
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
                        logger.info("exploration_status",
                                all_count=all_count,
                                interesting_count=interesting_count)
                self.logger.info("explored_source",
                        all_count=all_count, all_size=all_size,
                        interesting_count=interesting_count,
                        interesting_size=interesting_size)

                self.scanner.set_statistics(
                        supported_size=interesting_size,
                        supported_count=interesting_count,
                        relevant_size=all_size,
                        relevant_count=all_count,
                        relevant_unsupported_size=0,
                        relevant_unsupported_count=0)

                self.logger.info("fetching_items")
                for idx, h in enumerate(interesting):
                    url = urljoin(source.to_url() + "/",
                            str(h.get_relative_path()))
                    url = url.replace(mountpath, url)

                    url_object = self.scanner.mint_url(
                            url=url, mime_type=h.guess_type())
                    with h.follow(sm).make_stream() as s:
                        self.scanner.scan(s.read(), url_object)
                    self.logger.info("fetched_item", pos=idx + 1, total=interesting_count)
                self.logger.info("fetched_items")

            self.logger.info("awaiting_completion")
            from os2datascanner.projects.admin.adminapp.models.conversionqueueitem_model import ConversionQueueItem
            while True:
                remaining_queue_items = ConversionQueueItem.objects.filter(
                    status__in=[ConversionQueueItem.NEW,
                                ConversionQueueItem.PROCESSING],
                    url__scan=self.scanner.scan_object
                ).count()
                if not remaining_queue_items:
                    break
                else:
                    self.logger.info("still_awaiting_completion",
                            remaining=remaining_queue_items)
                    sleep(60)
        finally:
            self.logger.info("finished")
            self.scanner.done()

