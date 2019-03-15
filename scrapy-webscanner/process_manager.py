#!/usr/bin/env python3
# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )

"""Start up and manage queue processors to ensure they stay running.

Starts up multiple instances of each processor.
Restarts processors if they die or if they get stuck processing a single
item for too long.
"""

import os
import shutil
import sys
import subprocess
import time
import signal
import settings as scanner_settings

import django
from datetime import timedelta
from django.utils import timezone
from django.db import transaction, IntegrityError, DatabaseError
from django import db
from django.conf import settings as django_settings


base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"
django.setup()

os.umask(0o007)

from os2webscanner.models.conversionqueueitem_model import ConversionQueueItem
from os2webscanner.models.scans.scan_model import Scan


var_dir = django_settings.VAR_DIR

log_dir = os.path.join(var_dir, "logs")

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

processes_per_type = scanner_settings.NUMBER_OF_PROCESSES_PER_TYPE
processing_timeout = timedelta(minutes=20)

process_types = ('html', 'libreoffice', 'ocr', 'pdf', 'zip', 'text', 'csv', 'xml')

process_map = {}
process_list = []


def stop_process(p):
    """Stop the process."""
    if 'process_handle' not in p:
        print("Process %s already stopped" % p['name'])
        return

    phandle = p['process_handle']
    del p['process_handle']
    pid = phandle.pid
    # If running, stop it
    if phandle.poll() is None:
        print("Terminating process %s" % p['name'])
        phandle.terminate()
        phandle.wait()
    # Remove pid from process map
    if pid in process_map:
        del process_map[pid]
    # Set any ongoing queue-items for this process id to failed
    ongoing_items = ConversionQueueItem.objects.filter(
        status=ConversionQueueItem.PROCESSING,
        process_id=pid
    )
    # Remove the temp directories for the failed queue items
    for item in ongoing_items:
        # Log to occurrence log
        try:
            item.url.scan.log_occurrence(
                "QUEUE STOPPING: type <{0}>, URL: {1}".format(
                    item.type,
                    item.url.url
                )
            )
        except:
            item.url.scan.log_occurrence(
                "QUEUE STOPPING: url <{0}>".format(
                    item.url.url,
                )
            )

        # Clean up.
        item.delete_tmp_dir()

    ongoing_items.update(
        status=ConversionQueueItem.FAILED
    )

    # Close logfile and remove it
    if 'log_fh' in p:
        log_fh = p['log_fh']
        del p['log_fh']
        log_fh.close()


def start_process(p):
    """Start the process."""
    if 'process_handle' in p:
        raise BaseException(
            "Program %s is already running" % p['name']
        )

    print(("Starting process %s, (%s)" % (
        p['name'], " ".join(p['program_args'])
    )))

    log_file = os.path.join(log_dir, p['name'] + '.log')
    log_fh = open(log_file, 'a')

    process_handle = subprocess.Popen(
        p['program_args'],
        stdout=log_fh,
        stderr=log_fh
    )

    pid = process_handle.pid

    if process_handle.poll() is None:
        print(("Process %s started successfully, pid = %s" % (
            p['name'], pid
        )))
    else:
        print("Failed to start process %s, exiting" % p['name'])
        exit_handler()

    p['log_fh'] = log_fh
    p['process_handle'] = process_handle
    p['pid'] = pid
    process_map[pid] = p


def restart_process(processdata):
    """Stop and start the process."""
    stop_process(processdata)
    start_process(processdata)


def exit_handler(signum=None, frame=None):
    """Handle process manager exit signals by stopping all processes."""
    for p in process_list:
        stop_process(p)
    sys.exit(1)


signal.signal(signal.SIGTERM | signal.SIGINT | signal.SIGQUIT, exit_handler)


def main():
    """Main function."""
    # Delete all inactive scan's queue items to start with
    Scan.cleanup_finished_scans(timedelta(days=10000), log=True)

    for ptype in process_types:
        for i in range(processes_per_type):
            name = '%s%d' % (ptype, i)
            program = [
                'python',
                os.path.join(base_dir, 'scrapy-webscanner',
                             'process_queue.py'),
                ptype
            ]
            # Libreoffice takes the homedir name as second arg
            if "libreoffice" == ptype:
                program.append(name)
            p = {'program_args': program, 'name': name}
            process_map[name] = p
            process_list.append(p)

    for p in process_list:
        start_process(p)

    while True:
        sys.stdout.flush()
        sys.stderr.flush()
        db.reset_queries()
        for pdata in process_list:
            if pdata['process_handle'].poll() is not None:
                print(("Process %s has terminated, restarting it" % (
                    pdata['name']
                )))
                restart_process(pdata)

        stuck_processes = ConversionQueueItem.objects.filter(
            status=ConversionQueueItem.PROCESSING,
            process_start_time__lt=(
                timezone.localtime(timezone.now()) - processing_timeout
            ),
        )

        for p in stuck_processes:
            pid = p.process_id
            if pid in process_map:
                print("Process with pid %s is stuck, restarting" % pid)
                stuck_process = process_map[pid]
                restart_process(stuck_process)
            else:
                p.status = ConversionQueueItem.FAILED
                try:
                    p.url.scan.log_occurrence(
                        "PROCESS STUCK: type <{0}>, URL: {1}".format(
                            p.type,
                            p.url.url
                        )
                    )
                except:
                    p.url.scan.log_occurrence(
                        "PROCESS STUCK: url <{0}>".format(
                            p.url.url,
                        )
                    )
                # Clean up failed conversion temp dir
                if os.access(p.tmp_dir, os.W_OK):
                    shutil.rmtree(p.tmp_dir, True)
                p.save()
                # Clean up failed conversion temp dir
                p.delete_tmp_dir()

        try:
            with transaction.atomic():
                running_scans = Scan.objects.filter(
                    status=Scan.STARTED
                ).select_for_update(nowait=True)
                for scan in running_scans:
                    print('Scan has pid {}'.format(scan.pid))
                    if not scan.pid \
                            and not hasattr(scan, 'exchangescan'):
                        continue
                    try:
                        # Check if process is still running
                        os.kill(scan.pid, 0)
                    except OSError:
                        scan.set_scan_status_failed(
                            "SCAN FAILED: Process died with pid {}".format(scan.pid))
        except (DatabaseError, IntegrityError) as ex:
            print('Error occured while trying to kill process %s' % scan.pid)
            print('Error message %s' % ex)
            pass

        # Cleanup finished scans from the last minute
        Scan.cleanup_finished_scans(timedelta(minutes=1), log=True)

        Scan.pause_non_ocr_conversions_on_scans_with_too_many_ocr_items()

        time.sleep(10)


try:
    main()
except KeyboardInterrupt:
    pass
except django.db.utils.InternalError as e:
    print('django internal errror %s' % e)
