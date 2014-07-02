#!/usr/bin/env python
import os
import sys
import signal

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"

from scanner.processors import *
from scanner.processors.processor import Processor

queued_processor = Processor.processor_by_type(sys.argv[1])

if(len(sys.argv) > 2):
    setup_args = sys.argv[2:]
    queued_processor.setup_queue_processing(*setup_args)

try:
    queued_processor.process_queue()
except KeyboardInterrupt:
    pass
