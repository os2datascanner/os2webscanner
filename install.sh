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

    SYSTEM_PACKAGES=$(cat "$DIR/doc/SYSTEM_DEPENDENCIES")

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
        python3 -m venv "$VIRTUALENV"
    fi &&

    "$VIRTUALENV/bin/pip" install -U setuptools wheel pip &&
    "$VIRTUALENV/bin/pip" install -r "$DIR/doc/requirements.txt"
}

configure_development_environment() {
    echo "$0: configuring development environment"
    "$VIRTUALENV/bin/python" "$DIR/setup.py" develop
}

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
    if _psql_query "pg_database WHERE datname='os2datascanner'"; then
        echo "$0: PostgreSQL database 'os2datascanner' already exists"
    else
        echo "$0: creating PostgreSQL database 'os2datascanner'"
        sudo -Hu postgres createdb -O os2datascanner os2datascanner
    fi
}

configure_prometheus() {
    echo "$0: configuring Prometheus server"

    if _psql_query "pg_catalog.pg_roles WHERE rolname='prometheus'"; then
        echo "$0: PostgreSQL user 'prometheus' already exists"
    else
        echo "$0: creating and configuring PostgreSQL user 'prometheus'"
        # Copied and pasted from
        # /usr/share/doc/prometheus-postgres-exporter/README.Debian
        sudo -Hu postgres psql <<'END'
CREATE USER prometheus;
ALTER USER prometheus SET SEARCH_PATH TO prometheus,pg_catalog;

CREATE SCHEMA prometheus AUTHORIZATION prometheus;

CREATE FUNCTION prometheus.f_select_pg_stat_activity()
RETURNS setof pg_catalog.pg_stat_activity
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT * from pg_catalog.pg_stat_activity;
$$;

CREATE FUNCTION prometheus.f_select_pg_stat_replication()
RETURNS setof pg_catalog.pg_stat_replication
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT * from pg_catalog.pg_stat_replication;
$$;

CREATE VIEW prometheus.pg_stat_replication
AS
  SELECT * FROM prometheus.f_select_pg_stat_replication();

CREATE VIEW prometheus.pg_stat_activity
AS
  SELECT * FROM prometheus.f_select_pg_stat_activity();

GRANT SELECT ON prometheus.pg_stat_replication TO prometheus;
GRANT SELECT ON prometheus.pg_stat_activity TO prometheus;

END
    fi

    if sudo -H grep --silent "dbname=os2datascanner" /etc/default/prometheus-postgres-exporter; then
        echo "$0: no need to patch /etc/default/prometheus-postgres-exporter"
    else
        echo "$0: patching /etc/default/prometheus-postgres-exporter"
        sudo -H tee --append /etc/default/prometheus-postgres-exporter <<END
DATA_SOURCE_NAME='user=prometheus host=/run/postgresql dbname=os2datascanner'
END
    fi
    sudo -H systemctl restart prometheus-postgres-exporter.service

    if sudo -H grep --silent 'job_name: os2datascanner' /etc/prometheus/prometheus.yml; then
        echo "$0: no need to patch /etc/prometheus/prometheus.yml"
    else
        echo "$0: patching /etc/prometheus/prometheus.yml"
        sudo -H tee --append /etc/prometheus/prometheus.yml <<END

      - job_name: os2datascanner
        file_sd_configs:
          - files:
            - $(readlink --canonicalize "$DIR/var/prometheus")/*.yml
            - $(readlink --canonicalize "$DIR/var/prometheus")/*.json
END
        echo "$0: reloading prometheus configuration"
        sudo -H pkill -HUP prometheus
    fi
}

install_system_dependencies
install_python_environment
configure_development_environment
configure_database
configure_prometheus
