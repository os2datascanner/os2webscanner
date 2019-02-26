import logging
import multiprocessing

from twisted.internet import reactor, defer

from run import StartScan

from scanners.spiders.filespider import FileSpider
from scanners.scanner_types.filescanner import FileScanner


class StartFileScan(StartScan, multiprocessing.Process):
    """A scanner application which can be run."""

    def __init__(self, scan_id, logfile=None, last_started=None):
        """
        Initialize the scanner application.
        Takes scan id as input, which is directly related to the scan job id in the database.
        """

        super().__init__(scan_id, logfile, last_started)
        multiprocessing.Process.__init__(self)

    def run(self):
        """Updates the scan status and sets the pid.
        Run the scanner, blocking until finished."""
        super().run()
        self.scanner = FileScanner(self.scan_id)
        if self.scanner.scan_object.status is not "STARTED":
            self.scanner.scan_object.set_scan_status_start()

        self.start_filescan_crawlers()

        self.scanner.scan_object.set_scan_status_done()

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
