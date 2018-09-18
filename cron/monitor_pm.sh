#!/bin/bash
# NB: This script should be run as the user www-data.
DIR=$(dirname "${BASH_SOURCE[0]}")
FULL_DIR="$(cd "$DIR" && pwd)"
BASE_DIR=$(dirname "${FULL_DIR}")
RECIPIENTS=carstena@magenta.dk,danni@magenta.dk

# Check if process manager is running or not.
PSS=$(pgrep -f process_)

if [ -z "${PSS}" ]; 
then
    echo "Not running, starting ..."
    "${BASE_DIR}/scrapy-webscanner/start_process_manager.sh" &
    sleep 30
    cat | mail -t ${RECIPIENTS} -s "Process manager genstartet"  << EOF 

    Process manager kørte ikke på $HOSTNAME og er genstartet.

    I øjeblikket kører følgende process_manager-processer:

    $(ps aux | grep process_)

    med venlig hilsen
    Kron-dæmonen på ${HOSTNAME}.

EOF

#else 
#    echo "Running"
fi
# Log file must be placed in /var/ dir from Django settings.
#VAR_DIR=$(${BASE_DIR}/webscanner_site/manage.py get_var_dir)
#LOG_FILE="${VAR_DIR}/logs/summary_report_dispatch.log"
