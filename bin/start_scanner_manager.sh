#!/bin/bash
set -x
DIR=$(dirname "${BASH_SOURCE[0]}")
FULL_DIR="$(cd "$DIR" && pwd)"
BASE_DIR=$(dirname "${FULL_DIR}")

source "${BASE_DIR}/python-env/bin/activate"
VAR_DIR=$(${BASE_DIR}/webscanner_site/manage.py get_var_dir)

exec python "${FULL_DIR}/scanner_manager.py"
