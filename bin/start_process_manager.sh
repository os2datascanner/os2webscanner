#!/bin/bash
set -x
DIR=$(dirname "${BASH_SOURCE[0]}")
FULL_DIR="$(cd "$DIR" && pwd)"
BASE_DIR=$(dirname "${FULL_DIR}")

export DJANGO_SETTINGS_MODULE="webscanner.settings"

source "${BASE_DIR}/python-env/bin/activate"
VAR_DIR=$(${BASE_DIR}/manage.py get_var_dir)
python -m os2datascanner.engine.scrape.process_manager "${VAR_DIR}/logs/process_manager.log"

