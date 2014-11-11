#!/bin/bash

DIR=$(dirname "${BASH_SOURCE[0]}")
FULL_DIR="$(cd "$DIR" && pwd)"
BASE_DIR=$(dirname "${FULL_DIR}")
LOG_FILE="/var/lib/testwebscanner/logs/summary_report_dispatch.log"
source "${BASE_DIR}/python-env/bin/activate"

date >> ${LOG_FILE}
echo "--- START ---" >> ${LOG_FILE}
python "${BASE_DIR}/webscanner_site/manage.py" dispatch_summary_reports >> ${LOG_FILE}   2>&1
echo "--- SLUT ---" >> ${LOG_FILE}
