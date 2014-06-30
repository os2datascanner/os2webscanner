#!/usr/bin/env python
import os
import sys

# Include the Django app
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(base_dir + "/webscanner_site")
os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"

from scanner.processors.libreoffice import LibreOfficeProcessor

queued_processor = LibreOfficeProcessor("sethtest")
queued_processor.run()

