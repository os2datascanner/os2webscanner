#!/usr/bin/env bash

# Kill all LibreOffice (oosplash) processes belonging to scans that are no
# longer running.

# Note: The following lines are strongly dependent on the format of the output
# of the `ps` command.

LO_PROCESSES=$(ps aux | grep oosplash | awk '{ print $15; }' | cut -d / -f 5 | sort | uniq | cut -d _ -f 2)
RUNNING_SCANS=$(ps aux | grep "run\.py" | awk ' { print $13; }')

for SCAN_ID in $LO_PROCESSES
do
    if [[ -z $(echo $RUNNING_SCANS | grep -w $SCAN_ID) ]]
    then
        #sudo -u www-data kill -9 $(ps aux | grep oosplash | grep "scan_${SCAN_ID}" | awk ' { print $2; }')
        echo $(ps aux | grep oosplash | grep "scan_${SCAN_ID}" | awk ' { print $2; }')
    fi
done



