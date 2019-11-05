#!/usr/bin/env bash

set -e

PROJECT_DIR=$(dirname $(dirname $(realpath $0 )))

_psql_query() {
    [ "`sudo -Hu postgres psql --no-align --tuples-only --quiet --command "SELECT 'FOUND' FROM $1 LIMIT 1"`" = 'FOUND' ]
}

configure_database() {
    if _psql_query "pg_catalog.pg_roles WHERE rolname='os2datascanner'"; then
        echo "$0: PostgreSQL user 'os2datascanner' already exists"
    else
        echo "$0: creating PostgreSQL user 'os2datascanner'"
        sudo -Hu postgres createuser --pwprompt os2datascanner
    fi &&
    if _psql_query "pg_database WHERE datname='os2datascanner-report'"; then
        echo "$0: PostgreSQL database 'os2datascanner-report' already exists"
    else
        echo "$0: creating PostgreSQL database 'os2datascanner-report'"
        sudo -Hu postgres createdb -O os2datascanner os2datascanner-report
    fi
}

perform_django_migrations() {
    echo "$0: applying Django migrations"
    if "$PROJECT_DIR/bin/manage-report" showmigrations | sponge | grep --quiet '\[ \]'; then
        "$PROJECT_DIR/bin/manage-report" migrate
    else
        echo "$0: all Django migrations have been applied"
    fi
}

configure_database
perform_django_migrations
