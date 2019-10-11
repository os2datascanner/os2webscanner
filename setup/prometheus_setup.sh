#!/usr/bin/env bash

set -e

_psql_query() {
    [ "`sudo -Hu postgres psql --no-align --tuples-only --quiet --command "SELECT 'FOUND' FROM $1 LIMIT 1"`" = 'FOUND' ]
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
        VAR_DIR="`$DIR/bin/manage-admin get_var_dir`"
        # Yes, the indentation is significant in this YAML fragment (groan...)
        sudo -H tee --append /etc/prometheus/prometheus.yml <<END

  - job_name: os2datascanner
    file_sd_configs:
      - files:
        - $(readlink --canonicalize "$VAR_DIR/prometheus")/*.yml
        - $(readlink --canonicalize "$VAR_DIR/prometheus")/*.json
END
        echo "$0: reloading prometheus configuration"
        sudo -H pkill -HUP prometheus
    fi
}