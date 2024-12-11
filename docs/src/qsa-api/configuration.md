# QSA REST API : configuration

QSA web server can be configured thanks to the next environment variables:

| Mandatory  | Environment variable                   |         Description                                                              |
|------------|----------------------------------------|----------------------------------------------------------------------------------|
| Yes        | `QSA_QGISSERVER_URL`                   | QGIS Server URL                                                                  |
| Yes        | `QSA_QGISSERVER_PROJECTS_DIR`          | Storage location on the filesystem for QGIS projects/styles and QSA database     |
| No         | `QSA_LOGLEVEL`                         | Loglevel : DEBUG, INFO (default) or ERROR                                        |
| No         | `QSA_QGISSERVER_PROJECTS_PSQL_SERVICE` | PostgreSQL service to store QGIS projects                                        |
| No         | `QSA_QGISSERVER_MONITORING_PORT`       | Connection port for `qsa-plugin`                                                 |
| No         | `QSA_MAPPROXY_PROJECTS_DIR`            | Storage location on the filesystem for MapProxy configuration files              |
| No         | `QSA_MAPPROXY_CACHE_S3_BUCKET`         | Activate S3 cache for MapProxy if bucket is set                                  |
| No         | `QSA_MAPPROXY_CACHE_S3_DIR`            | S3 cache directory for MapProxy. Default to `/mapproxy/cache`                    |

<div class="warning">
MapProxy

Time dimension caching is not supported with S3 backend storage.
</div>

## PostgreSQL support {#postgresql-support}

When PostgreSQL support is enabled to store QGIS projects thanks to the
`QSA_QGISSERVER_PROJECTS_PSQL_SERVICE` environment variable, the directory
`QSA_QGISSERVER_PROJECTS_DIR` is only used to store the QSA SQLite database as
well as QGIS QML styles.

The PostgreSQL support relies on a `service` defined in a [PostgreSQL connection
service file](https://www.postgresql.org/docs/current/libpq-pgservice.html).

For example with `QSA_QGISSERVER_PROJECTS_PSQL_SERVICE=qsa_projects`, a proper
`qsa_projects` section is needed in `~/.pg_service.conf`:

```` conf
[qsa_projects]
host=localhost
port=5432
dbname=qsa_test
user=pblottiere
password=
````

A query string parameter can be used to specify a `schema` through the QSA API
(`public` is used by default).

<div class="warning">
Roadmap

In the future, the QSA database and QGIS styles will also be stored in
PostgreSQL when enabled.
</div>
