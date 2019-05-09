#!/bin/bash

BASE_DIR=$(cd $(dirname "${BASH_SOURCE[0]}")/..; pwd)

PYTHON=${BASE_DIR}/python-env/bin/python

export DJANGO_SETTINGS_MODULE="os2datascanner.sites.admin.settings"

exec $PYTHON -m os2datascanner.engine.scanner_manager "$@"
