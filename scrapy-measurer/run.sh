#!/bin/bash

REL_DIR=$( dirname "${BASH_SOURCE[0]}" )
PROJECT_DIR=$(cd "$REL_DIR/.." && pwd)

if [ "$VIRTUAL_ENV" == "" ]; then
    source "${PROJECT_DIR}/python-env/bin/activate"
fi


pushd "${PROJECT_DIR}/scrapy-measurer" > /dev/null
scrapy crawl -a start_url="$1" measuring-spider
popd > /dev/null