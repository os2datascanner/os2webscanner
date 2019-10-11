#!/usr/bin/env bash

set -e

failure() {
    echo "$0: installation failed"
}

trap failure ERR

DIR="$(dirname "${BASH_SOURCE[0]}")"
VIRTUALENV="$DIR/python-env"

install_system_dependencies() {
    # System dependencies. These are the packages we need that are not present
    # on a fresh Ubuntu install.
    echo "$0: installing system dependencies"

    SYSTEM_PACKAGES=$(cat "$DIR/requirements/system_dependencies.txt")

    sudo -H apt-get update
    for package in ${SYSTEM_PACKAGES[@]}
    do
        sudo -H apt-get -y install "$package" || return 1
    done
}

install_python_environment() {
    # Setup virtualenv, install Python packages necessary to run BibOS Admin.
    echo "$0: installing Python environment and dependencies"

    if [ -e "$VIRTUALENV/bin/python3" ]
    then
        echo "$0: Python environment already installed" 1>&2
    else
        python3 -m venv --system-site-packages "$VIRTUALENV"
    fi &&

    "$VIRTUALENV/bin/pip" install -U setuptools wheel pip &&
    "$VIRTUALENV/bin/pip" install -r "$DIR/requirements/requirements.txt"
}

configure_development_environment() {
    echo "$0: configuring development environment"

    # setup.py develop seems to assume that the current working directory is
    # the thing that should be copied into python-env, which can mean copying
    # references to files to which (say) a web server user has no access. Argh!
    pushd "$DIR"
    "$VIRTUALENV/bin/python" "$DIR/setup.py" develop
    popd
}

install_system_dependencies
install_python_environment
configure_development_environment