#!/usr/bin/env python
import os
import sys

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"

from scanner.processors import *
from scanner.processors.processor import Processor

queued_processor = Processor.processor_by_type(sys.argv[1])
queued_processor.process_queue()

