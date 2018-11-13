import os
import sys

import django


def load_webscanner_settings():
    """Load webscanner settings into environment"""
    base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.append(base_dir + "/webscanner_site")
    os.environ["DJANGO_SETTINGS_MODULE"] = "webscanner.settings"


def run_django_setup():
    """Load django setup and include django app"""
    django.setup()
