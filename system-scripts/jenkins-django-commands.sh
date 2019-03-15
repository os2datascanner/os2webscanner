#!/usr/bin/env bash

. python-env/bin/activate

python webscanner_site/manage.py collectstatic --noinput

python webscanner_site/manage.py migrate