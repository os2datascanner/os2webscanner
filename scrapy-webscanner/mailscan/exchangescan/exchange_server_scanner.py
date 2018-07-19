import logging
from .utils import init_logger
import multiprocessing

from .exchange_mailbox_scanner import ExportError, ExchangeMailboxScanner


class ExchangeServerScanner(multiprocessing.Process):
    """ Helper class to allow parallel processing of export
    This classes inherits from multiprocessing and helps to
    run a number of exporters in parallel """
    def __init__(self, user_queue, domain, exchange_scanner, start_date=None):
        multiprocessing.Process.__init__(self)
        self.logger = init_logger(self.__class__.__name__,
                                  exchange_scanner,
                                  logging.DEBUG)
        self.user_queue = user_queue
        self.scanner = None
        self.user_name = None
        self.start_date = start_date
        self.domain = domain
        self.exchange_scanner = exchange_scanner

    def run(self):
        while not self.user_queue.empty():
            try:
                self.user_name = self.user_queue.get()
                self.logger.info('Scanning {}'.format(self.user_name))

                self.scanner = ExchangeMailboxScanner(self.user_name,
                                                      self.domain,
                                                      self.exchange_scanner)

                total_count = self.scanner.total_mails()
                self.scanner.check_mailbox(total_count)
                self.logger.info('Done with {}'.format(self.user_name))
            except MemoryError:
                msg = 'We had a memory-error from {}'
                self.logger.error(msg.format(self.user_name))
                self.user_queue.put(self.user_name)
            except ExportError:
                msg = 'Could not export all of {}'
                self.logger.error(msg.format(self.user_name))
                self.user_queue.put(self.user_name)