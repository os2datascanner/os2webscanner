#!/usr/bin/env python
import os
import sys

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"

from os2webscanner.models import Scanner, Scan

import croniter
from datetime import datetime

def strip_seconds(d):
    """Remove any seconds or microseconds from the datetime"""
    return d.replace(second=0, microsecond=0)

from subprocess import Popen

now = strip_seconds(datetime.now())
print "Current time %s" % now

# Loop through all scanners
for scanner in Scanner.objects.all():
    # Skip scanners that are not scheduled
    if scanner.schedule == "":
        continue
    print "Scanner: %s; schedule: %s" % (scanner, scanner.schedule)

    try:
        # Parse the cron schedule expression
        cron = croniter.croniter(scanner.schedule, now)
    except ValueError as e:
        # This shouldn't happen because we should validate in the Web interface
        reason = "Invalid cron expression: %s" % e
        print reason
        scan = Scan(scanner=scanner, status=Scan.FAILED, reason=reason, start_time=datetime.now(), end_time=datetime.now())
        scan.save()
        continue

    # Check if it's time to run the scanner
    # Basically, just check if the next or previous scheduled time is the same as now
    next_run = strip_seconds(cron.get_next(datetime))
    if next_run != now:
        prev_run = strip_seconds(cron.get_prev(datetime))
        if prev_run != now:
            continue

    print "Running scanner %s" % scanner
    try:
        scan = Scan(scanner=scanner, status=Scan.NEW)
        scan.save()
        process = Popen(["./run.py", str(scan.id)])
        # Store pid
        scan.pid = process.pid
    except Exception, e:
        reason = repr(e)
        print reason
        scan.status = Scan.FAILED
        scan.reason = reason
    finally:
        scan.save()