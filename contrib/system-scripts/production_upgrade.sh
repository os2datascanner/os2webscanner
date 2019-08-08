#!/usr/bin/env bash

set -e

prod_dir=/srv/os2datascanner
repo_dir="$(dirname ${BASH_SOURCE[0]})/../../"


function prepare_ressources()
{
    sudo -H "$prod_dir/install.sh"
    sudo chown --recursive www-data:www-data "$prod_dir/"

    "$prod_dir/bin/manage-admin" collectstatic --noinput
    "$prod_dir/bin/manage-admin" makemessages --ignore=scrapy-webscanner/* --ignore=python-env/*
    "$prod_dir/bin/manage-admin" compilemessages
}

#
# PRODUCTION SETUP
#

function copy_to_prod_dir()
{
    echo "Copying to production dir $prod_dir..."
    sudo -H mkdir -p "$prod_dir"
    sudo -H rsync \
        --progress --recursive --delete  \
        --links --safe-links \
        --exclude ".git/" \
        --exclude "var/" \
        --exclude "python-env/" \
        --exclude '*.pyc' \
        --exclude "src/os2datascanner/projects/admin/local_settings.py" \
        "$repo_dir"/ "$prod_dir"
    sudo -H mkdir -p "$prod_dir/var"
    echo 'Done Copying.'
}

function restart_ressources()
{
    echo 'Restarting services...'

    # Everything here is allowed to fail
    sudo pkill python || true
    sudo pkill soffice.bin || true

    sudo service datascanner-manager restart || true
    sudo service supervisor reload || true
    sudo service apache2 reload || true
    echo 'Services restarted.'
}

copy_to_prod_dir
prepare_ressources
restart_ressources
