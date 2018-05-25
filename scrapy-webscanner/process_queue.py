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

"""Program which processes the queue of the given type (argument 1).

Pass extra arguments to the processor after the first argument.
"""

import os
import sys
import django

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"
django.setup()

from scanner.processors.processor import Processor

pid = os.getpid()

queued_processor = Processor.processor_by_type(sys.argv[1])

setup_args = [pid]
if(len(sys.argv) > 2):
    setup_args.extend(sys.argv[2:])


if queued_processor is not None:
    queued_processor.setup_queue_processing(*setup_args)
    try:
        queued_processor.process_queue()
    except KeyboardInterrupt:
        pass
