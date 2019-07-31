from time import sleep
import multiprocessing
from urllib.parse import urljoin, quote

from .run import StartScan

from ..engine2.model.core import SourceManager, ResourceUnavailableError
from ..engine2.model.http import WebSource
from ..engine2.model.smbc import SMBCSource
from .scanners.processors.processor import Processor
from .scanners.scanner_types.webscanner import WebScanner
from .scanners.scanner_types.filescanner import FileScanner

import structlog
logger = structlog.get_logger()


class StartEngine2Scan(StartScan, multiprocessing.Process):
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

        self.scanner = _make_scanner(self.configuration)
        source = _make_source(self.configuration, self.scanner)

        try:
            with SourceManager() as sm:
                interesting = None

                if hasattr(self.scanner, 'set_statistics'):
                    # If our scanner is interested in collecting statistics,
                    # then do a pre-analysis pass
                    interesting = []

                    all_size = 0
                    all_count = 0

                    interesting_size = 0
                    interesting_count = 0

                    self.logger.info("exploring_source")
                    for h in source.handles(sm):
                        mime = h.guess_type()
                        try:
                            size = h.follow(sm).get_size()
                            all_size += size
                            all_count += 1
                        except ResourceUnavailableError:
                            continue
                        if Processor.mimetype_to_processor_type(mime):
                            interesting_size += size
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
                else:
                    # If not, then just return the generator directly
                    interesting = source.handles(sm)

                self.logger.info("fetching_items")
                for idx, handle in enumerate(interesting):
                    url = self.make_presentation_url(handle)

                    url_object = self.scanner.mint_url(
                            url=url, mime_type=handle.guess_type())
                    try:
                        with handle.follow(sm).make_stream() as s:
                            self.scanner.scan(s.read(), url_object)
                        self.logger.info("fetched_item",
                                path=handle.get_relative_path(), pos=idx + 1)
                    except ResourceUnavailableError:
                        if hasattr(handle, 'get_referrer_urls'):
                            pass # XXX: actually build referrer URL structure
                        self.logger.info("item_unavailable",
                            path=handle.get_relative_path(), pos=idx + 1)
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

    def make_presentation_url(self, handle):
        variety = self.configuration['type']
        if variety == 'WebScanner':
            return urljoin(handle.get_source().to_url() + "/",
                    handle.get_relative_path())
        elif variety == 'FileScanner':
            return urljoin("file:" + quote(handle.get_source().get_unc()) + "/",
                    quote(handle.get_relative_path()))
        else:
            raise Exception("Unknown variety {0}".format(variety))

def _make_scanner(configuration):
    variety = configuration['type']

    scanner = None
    if variety == 'WebScanner':
        scanner = WebScanner(configuration)
    elif variety == 'FileScanner':
        scanner = FileScanner(configuration)
    else:
        raise Exception("Unknown variety {0}".format(variety))

    scanner.ensure_started()
    return scanner

def _make_source(configuration, scanner):
    variety = configuration['type']

    if variety == 'WebScanner':
        return WebSource(scanner.get_scanner_object().url)
    elif variety == 'FileScanner':
        db_object = scanner.get_scanner_object()
        return SMBCSource(db_object.url,
                user=db_object.authentication.username,
                password=db_object.authentication.get_password(),
                domain=db_object.authentication.domain)
    else:
        raise Exception("Unknown variety {0}".format(variety))
