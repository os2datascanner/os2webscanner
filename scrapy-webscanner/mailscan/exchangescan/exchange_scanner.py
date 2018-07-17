import os
import sys
import time
import logging
import django
from multiprocessing import Queue
from pathlib import Path

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(os.path.join(__file__, "../../"))))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"
django.setup()

from os2webscanner.models.scan_model import Scan

from ...settings import NUMBER_OF_EMAIL_THREADS
from ...scanner.scanner.scanner import Scanner
from .exchange_server_scanner import ExchangeServerScanner

logger = logging.Logger('Exchange_scanner')


class ExchangeScanner:
    """A scanner application which can be run."""

    def __init__(self):
        """
        Initialize the scanner application.
        Takes input, argv[1], which is directly related to the scan job id in the database.
        Updates the scan status and sets the pid.
        """
        self.scan_id = sys.argv[1]

        # Get scan object from DB
        self.scan_object = Scan.objects.get(pk=self.scan_id)
        self.scan_object.set_scan_status_start()
        self.scanner = Scanner(self.scan_id)

    def read_users(user_queue, user_file):
        """ Small helper to read user-list from file
        :param user_queue: The common multiprocess queue
        :param user_file: Filename for user list
        """
        user_path = Path(user_file)
        with user_path.open('r') as f:
            users = f.read().split('\n')
        for user in users:
            if len(user.strip()) == 0:
                users.remove(user)
        for user in users:
            user_queue.put(user)

    def run(self):
        domains = self.scanner.get_domains()
        for domain in domains:
            user_queue = Queue()
            self.read_users(domain.exchangedomain.userlist, user_queue)
            scanners = {}
            for i in range(0, NUMBER_OF_EMAIL_THREADS):
                scanners[i] = ExchangeServerScanner(user_queue, domain, self.scanner, None)
                # stats.add_scanner(scanners[i])
                scanners[i].start()
                time.sleep(1)


exchange_scanner = ExchangeScanner()
exchange_scanner.run()
