#!/bin/bash

DIR=$(dirname "${BASH_SOURCE[0]}")
FULL_DIR="$(cd "$DIR" && pwd)"
BASE_DIR=$(dirname "${FULL_DIR}")

source "${BASE_DIR}/python-env/bin/activate"
python "${FULL_DIR}/process_manager.py" >"${BASE_DIR}/var/logs/process_manager.log" 2>&1

