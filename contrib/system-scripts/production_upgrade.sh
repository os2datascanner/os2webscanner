#!/usr/bin/env bash

prod_dir=/srv/os2datascanner
repo_dir=`cat .pwd`
install_dir=$repo_dir


function prepare_ressources()
{

    ./install.sh

    # Migrate
    source $prod_dir/python-env/bin/activate

    managepy=django-admin

    $managepy collectstatic --noinput
    $managepy makemigrations --merge
    $managepy migrate

    $managepy makemessages --ignore=scrapy-webscanner/* --ignore=python-env/*
    $managepy compilemessages

}

#
# PRODUCTION SETUP
#

function copy_to_prod_dir()
{

    echo 'Coyping to prod dir...'
    sudo cp --recursive -u www-data src bin contrib $prod_dir
    sudo cp NEWS LICENSE README VERSION $prod_dir

    sudo chown --recursive www-data:www-data $prod_dir
    echo 'Done Coyping.'

}

function restart_ressources()
{
    echo 'Restarting services...'
    sudo pkill python
    sudo pkill soffice.bin

    sudo service datascanner-manager restart
    sudo service supervisor reload
    sudo service apache2 reload
    echo 'Services restarted.'
}

prepare_ressources
copy_to_prod_dir
restart_ressources
