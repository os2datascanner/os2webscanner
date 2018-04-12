#!/usr/bin/env python
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

"""Program meant to be run once a minute by cron.

Starts spiders scheduled to run during the current minute.
"""

import os
import sys

import datetime
from dateutil.rrule import *  # noqa

import django

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"
django.setup()


from os2webscanner.models import Scanner


def strip_seconds(d):
    """Remove any seconds or microseconds from the datetime."""
    return d.replace(second=0, microsecond=0)


current_qhr = strip_seconds(datetime.datetime.now())
current_qhr = current_qhr.replace(
    minute=current_qhr.minute - current_qhr.minute % 15
)

next_qhr = current_qhr + datetime.timedelta(
    minutes=15, microseconds=-1
)

# Loop through all scanners
for scanner in Scanner.objects.exclude(schedule=""):
    # Skip scanners that should not start now
    start_time = scanner.get_start_time()
    if start_time < current_qhr.time() or start_time > next_qhr.time():
        continue

    try:
        # Parse the recurrence rule expression
        schedule = scanner.schedule
    except ValueError as e:
        # This shouldn't happen because we should validate in the UI
        reason = "Invalid schedule expression: %s" % e
        print(reason)
        continue

    # We have to set the times of the specific dates to the start time in
    # order for the recurrence rule check to work
    for i in range(len(schedule.rdates)):
        rdate = schedule.rdates[i]
        schedule.rdates[i] = rdate.replace(hour=start_time.hour,
                                           minute=start_time.minute)

    # Check if it's time to run the scanner
    if not schedule.between(
        current_qhr, next_qhr,
        # Generate recurrences starting from current quarter 2014/01/01
        dtstart=datetime.datetime(
            2014, 1, 1, current_qhr.hour, current_qhr.minute), inc=True
    ):
        continue

    print("Running scanner %s" % scanner)
    scanner.run()
