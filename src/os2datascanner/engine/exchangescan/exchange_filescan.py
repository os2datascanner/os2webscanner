"""
VIGTIGT!!!!
Denne fil bruges ikke mere nogen steder og skal heller ikke bruges fremadrettet.
Gemmes kun midlertidigt indtil anden implementation virker efter hensigten.

Demands:
* starter når den første _done folder er markeret
* hvis filscan indhenter exchange download skal filscan vente indtil en ny folder er markeret med _done.
* Når alt exchange indhold er downloadet skal filscan vide at der ikke er mere indhold at scanne.
"""
import os
import time
import queue
import multiprocessing
import django

from django.core.exceptions import ObjectDoesNotExist

from exchangelib import EWSDate

from .mailscan_exchange import ExchangeServerScan, read_users
from .settings import NUMBER_OF_EMAIL_THREADS
from os2datascanner.sites.admin.adminapp.models.domain_model import Domain


class ExchangeFilescanner(multiprocessing.Process):

    def __init__(self, scan_id):
        multiprocessing.Process.__init__(self)
        print('Program started')
        self.scan_id = scan_id
        django.setup()
        from os2datascanner.sites.admin.adminapp.models.scan_model import Scan
        scan_object = Scan.objects.get(pk=self.scan_id)
        valid_domains = scan_object.domains.filter(
            validation_status=Domain.VALID
        )

        """Making scan dir if it does not exists"""
        if not os.path.exists(scan_object.scan_dir):
            print('Creating scan dir {}'.format(scan_object.scan_dir))
            os.makedirs(scan_object.scan_dir)

        scan_dir = scan_object.scan_dir + '/'

        """Handling last scannings date"""
        last_scannings_date = None
        if scan_object.do_last_modified_check:
            last_scannings_date = scan_object.exchangescan.last_scannings_date
            if last_scannings_date:
                last_scannings_date = EWSDate.from_date(
                    last_scannings_date)

        """Foreach domain x number of mail processors are started."""
        for domain in valid_domains:
            credentials = (domain.authentication.username,
                           domain.authentication.get_password())
            self.user_queue = multiprocessing.Queue()
            read_users(self.user_queue,
                       domain.exchangedomain.get_userlist_file_path())
            self.done_queue = multiprocessing.Queue()
            mail_ending = domain.url

            scanners = {}
            for i in range(0, NUMBER_OF_EMAIL_THREADS):
                scanners[i] = ExchangeServerScan(credentials,
                                                 self.user_queue,
                                                 self.done_queue,
                                                 scan_dir,
                                                 mail_ending,
                                                 start_date=
                                                 last_scannings_date)
                scanners[i].start()
                print('Started scanner {}'.format(i))
                time.sleep(1)

            self.scanners = scanners
            print('Scanners started...')

    def run(self):
        """
        Starts an exchange mail server scan.
        """

        """
        As long as mail scanners are running file scanners will be started 
        when there is something in the shared queue.
        """
        django.setup()
        for key, value in self.scanners.items():
            self.start_folder_scan(self.done_queue)

            while value.is_alive():
                print('Process with pid {} is still alive'.format(value.pid))
                self.start_folder_scan(self.done_queue)
                time.sleep(1)

        self.mark_scan_job_as_done(True)

    def start_folder_scan(self, q):
        """
        Getting next queue item and starting file scan on item, until queue is empty.
        :param q: shared queue
        """
        item = q.get()
        while item is not None:
            print('Getting item from q: {}'.format(item))
            try:
                self.start_filescan(item)
                item = q.get(True, 1)

            except queue.Empty:
                print('Queue is empty')
                item = None

    def start_filescan(self, path):
        """
        Starts a file scan on downloaded exchange folder
        :param path: path to folder
        """
        self.update_scan_job_path(path)
        print('Starting file scan for path {}'.format(path))
        import json
        from os2datascanner.sites.admin.adminapp.amqp_communication import amqp_connection_manager
        queue_name = 'datascanner'
        message = {'type': 'FileScanner', 'id': self.scan_id}
        amqp_connection_manager.start_amqp(queue_name)
        amqp_connection_manager.send_message(queue_name, json.dumps(message))
        amqp_connection_manager.close_connection()

    def update_scan_job_path(self, path):
        """
        When an exchange users data has been downloaded
        the path to the downloaded files are stored.
        :param path: path to downloaded files
        :return: scan_object with updated folder_to_scan path
        """
        try:
            scan_object = self.get_scan_object()
            scan_object.folder_to_scan = str(path)
            scan_object.save()
        except Exception as ex:
            print('Error occured while storing path to scan: {}'.format(path))
            print(ex)
        return scan_object

    def get_scan_object(self):
        """Gets the scan object from db"""
        try:
            from os2datascanner.sites.admin.adminapp.models.exchangescan_model import ExchangeScan
            scan_object = ExchangeScan.objects.get(pk=self.scan_id)
        except ObjectDoesNotExist:
            print('Scan object with id {} does not exists.'.format(
                self.scan_id)
            )
        return scan_object

    def mark_scan_job_as_done(self, is_done):
        """
        Marks the exchange scan job as done
        :param is_done: boolean value marking the job as completed or not.
        :return: the updated scan_object.
        """
        try:
            scan_object = self.get_scan_object()
            scan_object.mark_scan_as_done = is_done
            scan_object.save()
        except Exception as ex:
            print('Error occured while storing path to scan: {}'.format(is_done))
            print(ex)
        return scan_object

# TODO: læg user elementer i en python list og tjek tilsidst eller løbende at alle users er scannet.
