#!/bin/bash

BASE_DIR=$(cd $(dirname "${BASH_SOURCE[0]}")/..; pwd)

export DJANGO_SETTINGS_MODULE="os2datascanner.projects.admin.settings"

exec ${BASE_DIR}/python-env/bin/django-admin scanner_manager "$@"
