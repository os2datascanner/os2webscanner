#!/usr/bin/env bash

. python-env/bin/activate

python webscanner_site/manage.py makemessages --ignore=scrapy-webscanner/* --ignore=python-env/*