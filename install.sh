#!/usr/bin/env bash

DIR=$(dirname ${BASH_SOURCE[0]})
VIRTUALENV=./python-env

# System dependencies. These are the packages we need that are not present on a
# fresh Ubuntu install.

SYSTEM_PACKAGES=$(cat "$DIR/doc/SYSTEM_DEPENDENCIES")

for package in "${SYSTEM_PACKAGES[@]}"
do
    sudo apt-get -y install $package
done

# Setup virtualenv, install Python packages necessary to run BibOS Admin.
if [ -e $VIRTUALENV/bin/python3 ]
then
    echo "virtual environment already installed" 1>&2
else
    python3 -m venv $VIRTUALENV
fi

"$VIRTUALENV/bin/pip" install -r "$DIR/doc/requirements.txt"

if [ $? -ne 0 ]; then
    echo "" 1>&2
    echo "ERROR: Unable to install Python package <$package>." 1>&2
    echo -n "Please check your network connection. " 1>&2
    echo "A remote server may be down - please retry later. " 1>&2
    echo "" 1>&2
    exit -1
fi

"$VIRTUALENV/bin/python" "$DIR/setup.py" develop
