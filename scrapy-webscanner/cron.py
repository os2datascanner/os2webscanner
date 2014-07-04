#!/usr/bin/env python

"""Program meant to be run once a minute by cron.

Starts spiders scheduled to run during the current minute.
"""

import os
import sys

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"

from os2webscanner.models import Scanner, Scan

from datetime import datetime
from dateutil.rrule import *
from dateutil.relativedelta import relativedelta


def strip_seconds(d):
    """Remove any seconds or microseconds from the datetime."""
    return d.replace(second=0, microsecond=0)


current_minute = strip_seconds(datetime.now())
print "Current time %s" % current_minute

# Loop through all scanners
for scanner in Scanner.objects.all():
    # Skip scanners that are not scheduled
    if scanner.schedule.strip() == "":
        continue
    print "Scanner: %s; schedule: %s" % (scanner, scanner.schedule)

    try:
        # Parse the recurrence rule expression
        rule = rrulestr(scanner.schedule)
    except ValueError as e:
        # This shouldn't happen because we should validate in the UI
        reason = "Invalid schedule expression: %s" % e
        print reason
        continue

    # Get the start of the next minute
    next_minute = strip_seconds(current_minute + relativedelta(minutes=+1))

    # Subtract 1 microsecond, so we don't include jobs starting at the
    # start of the next minute
    next_minute = next_minute - relativedelta(microseconds=1)

    # Check if it's time to run the scanner
    if not rule.between(current_minute, next_minute, inc=True):
        continue

    print "Running scanner %s" % scanner
    scanner.run()
