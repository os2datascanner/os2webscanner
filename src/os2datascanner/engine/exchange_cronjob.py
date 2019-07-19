#!/usr/bin/env python
""" Exchange cron job downloads exchange content on regular basis.

"""
import os
import time
import shutil
import multiprocessing

from os2datascanner.engine.exchangescan import settings
from os2datascanner.engine.exchangescan.export_exchange_content import ExchangeServerExport, read_users

from os2datascanner.engine.utils import run_django_setup

run_django_setup()

from os2datascanner.projects.admin.adminapp.models.scannerjobs.scanner_model import Scanner
from os2datascanner.projects.admin.adminapp.models.scannerjobs.exchangescanner_model import ExchangeScanner


def start_exchange_export():
    """Starts the exchange server export"""

    # Collect credentials
    credentials = (exchange_scanner.authentication.username,
                   exchange_scanner.authentication.get_password())

    # Create use queue and load in users.
    user_queue = multiprocessing.Queue()
    read_users(user_queue,
               exchange_scanner.get_userlist_file_path())

    done_queue = multiprocessing.Queue()

    mail_ending = exchange_scanner.url

    # TODO: Make an intelligent usage of last_export_date, where you consider how to handle user_list is updated.
    last_export_date = None

    export_dir = os.path.join(settings.EXCHANGE_EXPORT_DIR_PREFIX,
                              mail_ending.replace('@', ''))
    # Make export dir export ready
    if os.path.isdir(export_dir):
        shutil.rmtree(export_dir)
    os.mkdir(export_dir)

    exchange_scanner.is_exporting = True
    exchange_scanner.is_ready_to_scan = False
    exchange_scanner.save()
    scanners = {}

    for i in range(0, settings.NUMBER_OF_EMAIL_THREADS):
        scanners[i] = ExchangeServerExport(credentials,
                                           user_queue,
                                           done_queue,
                                           export_dir + '/',
                                           mail_ending,
                                           start_date=
                                           last_export_date)
        scanners[i].start()
        print('Started exchange export {}'.format(i))
        time.sleep(1)

    print('All {} export-processors started...'.format(
        str(settings.NUMBER_OF_EMAIL_THREADS)))

    for key, value in scanners.items():
        while value.is_alive():
            print('Process with pid {} is still alive'.format(value.pid))
            time.sleep(60)

    exchange_scanner.dir_to_scan = export_dir
    exchange_scanner.save()

    exchange_scanner.is_exporting = False
    exchange_scanner.is_ready_to_scan = True
    exchange_scanner.save()


for exchange_scanner in ExchangeScanner.objects.filter(
                            validation_status=Scanner.VALID):
    """Foreach scan, x number of mail processors are started."""
    if not exchange_scanner.is_exporting and not exchange_scanner.is_running:
        start_exchange_export()
    else:
        print('Exchange export is already in progress '
              'for exchange scanner {}'.format(exchange_scanner.name)
              )
