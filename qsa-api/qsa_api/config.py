# coding: utf8

import os
import logging
from pathlib import Path


class QSAConfig:
    @property
    def is_valid(self) -> bool:
        if self.qgisserver_url and self.qgisserver_projects_dir:
            return True
        return False

    @property
    def loglevel(self):
        level = os.environ.get("QSA_LOGLEVEL", "INFO").lower()

        logging_level = logging.INFO
        if level == "debug":
            logging_level = logging.DEBUG
        elif level == "error":
            logging_level = logging.ERROR
        return logging_level

    @property
    def gdal_pam_proxy_dir(self) -> Path:
        return Path(os.environ.get("GDAL_PAM_PROXY_DIR", ""))

    @property
    def monitoring_port(self) -> int:
        return int(os.environ.get("QSA_QGISSERVER_MONITORING_PORT", "0"))

    @property
    def qgisserver_url(self) -> str:
        return os.environ.get("QSA_QGISSERVER_URL", "")

    @property
    def qgisserver_projects_dir(self) -> str:
        return os.environ.get("QSA_QGISSERVER_PROJECTS_DIR", "")

    @property
    def qgisserver_projects_psql_service(self) -> str:
        return os.environ.get("QSA_QGISSERVER_PROJECTS_PSQL_SERVICE", "")
    @property
    def qgisserver_projects_psql_dbname(self) -> str:
        return os.environ.get("QSA_QGISSERVER_PROJECTS_PSQL_DBNAME", "")
    @property
    def qgisserver_projects_psql_user(self) -> str:
        return os.environ.get("QSA_QGISSERVER_PROJECTS_PSQL_USER", "")
    @property
    def qgisserver_projects_psql_password(self) -> str:
        return os.environ.get("QSA_QGISSERVER_PROJECTS_PSQL_PASSWORD", "")
    @property
    def qgisserver_projects_psql_host(self) -> str:
        return os.environ.get("QSA_QGISSERVER_PROJECTS_PSQL_HOST", "")
    @property
    def qgisserver_projects_psql_port(self) -> str:
        return os.environ.get("QSA_QGISSERVER_PROJECTS_PSQL_PORT", "")
    @property
    def mapproxy_projects_dir(self) -> str:
        return os.environ.get("QSA_MAPPROXY_PROJECTS_DIR", "").replace('"', "")

    @property
    def mapproxy_cache_s3_bucket(self) -> str:
        return os.environ.get("QSA_MAPPROXY_CACHE_S3_BUCKET", "")

    @property
    def mapproxy_cache_s3_dir(self) -> str:
        return os.environ.get("QSA_MAPPROXY_CACHE_S3_DIR", "/mapproxy/cache")

    @property
    def aws_access_key_id(self) -> str:
        return os.environ.get("AWS_ACCESS_KEY_ID", "")

    @property
    def aws_secret_access_key(self) -> str:
        return os.environ.get("AWS_SECRET_ACCESS_KEY", "")
