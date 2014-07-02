#!/usr/bin/env python

import os
import sys
import subprocess
import time
import signal
from datetime import timedelta
from django.utils import timezone

base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"

from os2webscanner.models import ConversionQueueItem

var_dir = os.path.join(base_dir, "var")
log_dir = os.path.join(var_dir, "logs")

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

processes_per_type = 5
seconds_until_stuck = 60

process_types = ('html', 'libreoffice', 'ocr', 'pdf')

process_map = {}
process_list = []

def stop_process(pdata):
    if not 'process_handle' in pdata:
        print "Process %s already stopped" % pdata['name']
        return

    phandle = pdata['process_handle']
    del pdata['process_handle']
    pid = phandle.pid
    # If running, stop it
    if phandle.poll() is None:
        print "Terminating process %s" % pdata['name']
        phandle.terminate()
        phandle.wait()
    # Remove pid from process map
    if pid in process_map:
        del process_map[pid]

    # Close logfile and remove it
    if 'log_fh' in pdata:
        log_fh = pdata['log_fh']
        del pdata['log_fh']
        log_fh.close()

def start_process(pdata):
    if 'process_handle' in pdata:
        raise BaseException(
            "Program %s is already running" % pdata['name']
        )

    print "Starting process %s, (%s)" % (
        pdata['name'], " ".join(pdata['program_args'])
    )

    log_file = os.path.join(log_dir, pdata['name'] + '.log')
    log_fh = open(log_file, 'a')

    process_handle = subprocess.Popen(
        pdata['program_args'],
        stdout=log_fh,
        stderr=log_fh
    )

    if process_handle.poll() is None:
        print "Process %s started successfully, pid = %s" % (
            pdata['name'], process_handle.pid
        )
    else:
        print "Failed to start process %s, existing" % pdata['name']
        exit_handler()

    pdata['log_fh'] = log_fh
    pdata['process_handle'] = process_handle
    pdata['pid'] = process_handle.pid
    process_map[process_handle.pid] = process_data

def restart_process(pdata):
    stop_process(pdata)
    start_process(pdata)

def exit_handler(signum, frame):
    for pdata in process_list:
        stop_process(pdata)
    sys.exit(1)

signal.signal(signal.SIGTERM | signal.SIGINT | signal.SIGQUIT, exit_handler)

for ptype in process_types:
    for i in range(processes_per_type):
        name = '%s%d' % (ptype, i)
        program = [
            'python',
            os.path.join(base_dir, 'scrapy-webscanner', 'process_queue.py'),
            ptype
        ]
        # Libreoffice takes the homedir name as second arg
        if "libreoffice" == ptype:
            program.append(name)
        process_data = { 'program_args': program, 'name': name }
        process_map[name] = process_data
        process_list.append(process_data)

for pdata in process_list:
    start_process(pdata)

try:
    while True:
        for pdata in process_list:
            result = pdata['process_handle'].poll()
            if pdata['process_handle'].poll() is not None:
                print "Process %s has terminated, restarting it" % pdata['name']
                restart_process(pdata)
        stuck_processes = ConversionQueueItem.objects.filter(
            status=ConversionQueueItem.PROCESSING,
            process_start_time__lt=timezone.now() - timedelta(
                0, seconds_until_stuck
            ),
            process_id__in=[ pdata['pid'] for pdata in process_list ]
        )
        for p in stuck_processes:
            restart_process(process_map[p.process_id])
        time.sleep(10)
except KeyboardInterrupt:
    pass

