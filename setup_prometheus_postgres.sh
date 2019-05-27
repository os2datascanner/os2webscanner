#!/bin/sh

set -e

if [ "`id -u`" != "0" ]; then
    echo "$0: must, unfortunately, be root" 1>&2
    exit 1
fi

echo "$0: setting up prometheus PostgreSQL user"

# Copied and pasted from
# /usr/share/doc/prometheus-postgres-exporter/README.Debian
sudo -u postgres psql -vON_ERROR_STOP=1 <<'END'

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

cat <<END >> /etc/default/prometheus-postgres-exporter
DATA_SOURCE_NAME='user=prometheus host=/run/postgresql dbname=os2webscanner'
END

systemctl restart prometheus-postgres-exporter.service

if grep --silent 'job_name: os2datascanner' /etc/prometheus/prometheus.yml; then
    echo "$0: no need to patch /etc/prometheus/prometheus.yml"
else
    echo "$0: patching /etc/prometheus/prometheus.yml"
    cat <<END >> /etc/prometheus/prometheus.yml

  - job_name: os2datascanner
    file_sd_configs:
      - files:
        - $(readlink --canonicalize "$(dirname "$0")/prometheus")/*.yml
        - $(readlink --canonicalize "$(dirname "$0")/prometheus")/*.json
END
    echo "$0: reloading prometheus configuration"
    killall -HUP prometheus
fi
