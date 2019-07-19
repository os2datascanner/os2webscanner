#!/bin/bash

DIR="$(dirname "$(dirname "${BASH_SOURCE[0]}")")"
FULL_DIR="$(cd "$DIR" && pwd)"
BASE_DIR=$(dirname "${FULL_DIR}")

source "${BASE_DIR}/python-env/bin/activate"
python "${BASE_DIR}/src/os2datascanner/engine/exchange_cronjob.py"
