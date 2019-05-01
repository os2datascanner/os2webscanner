import logging
import multiprocessing

from twisted.internet import reactor, defer

from .run import StartScan

from .scanners.spiders.filespider import FileSpider
from .scanners.scanner_types.filescanner import FileScanner


class StartFileScan(StartScan, multiprocessing.Process):
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
        self.start_filescan_crawlers()
        self.scanner.done()

    def start_filescan_crawlers(self):
        """Start a file scan."""

        logging.info("Beginning crawler process.")
        self.run_crawlers()
        self.crawler_process.start()
        logging.info("Crawler process finished.")

    @defer.inlineCallbacks
    def run_crawlers(self):
        self.make_scanner_crawler(FileSpider)
        yield self.crawler_process.crawl(self.scanner_crawler,
                                         scanner=self.scanner,
                                         runner=self)

    def handle_closed(self, spider, reason):
        """Handle the spider being finished."""
        self.filescan_cleanup()
        super().handle_closed(spider, reason)

    def filescan_cleanup(self):
        for domain in self.scanner.valid_domains:
            domain.filedomain.smb_umount()
