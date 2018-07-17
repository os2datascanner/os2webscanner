#!/bin/bash

# Script to run run.py inside the virtualenv

source ../python-env/bin/activate
python exchange_scanner.py $@
