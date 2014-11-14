#!/bin/bash

DIR=$(dirname "${BASH_SOURCE[0]}")
FULL_DIR="$(cd "$DIR" && pwd)"
BASE_DIR=$(dirname "${FULL_DIR}")

# Activate virtualenv
source "${BASE_DIR}/python-env/bin/activate"

# Log file must be placed in /var/ dir from Django settings.
VAR_DIR=$(${BASE_DIR}/webscanner_site/manage.py get_var_dir)
LOG_FILE="${VAR_DIR}/logs/summary_report_dispatch.log"

date >> ${LOG_FILE}
echo "--- START ---" >> ${LOG_FILE}
python "${BASE_DIR}/webscanner_site/manage.py" dispatch_summary_reports >> ${LOG_FILE}   2>&1
echo "--- SLUT ---" >> ${LOG_FILE}
