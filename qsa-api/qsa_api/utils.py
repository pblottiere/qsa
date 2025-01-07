# coding: utf8

import os
import sys
import boto3
import logging
import threading
from enum import Enum
from pathlib import Path
from flask import current_app
from botocore.exceptions import ClientError

from .config import QSAConfig


def config():
    return current_app.config["CONFIG"]


def logger():
    return current_app.logger


def s3_parse_uri(uri: str):
    # /vsis3/{bucket}/{subdirs}/{filename}
    bucket = uri.split("/")[2]
    subdirs = Path(uri.split(f"/vsis3/{bucket}/")[1]).parent.as_posix()
    filename = Path(uri.split(f"/vsis3/{bucket}/")[1]).name
    return bucket, subdirs, filename


class StorageBackend(Enum):
    FILESYSTEM = 0
    POSTGRESQL = 1

    @staticmethod
    def type() -> "StorageBackend":
        if config().qgisserver_projects_psql_service:
            return StorageBackend.POSTGRESQL
        return StorageBackend.FILESYSTEM


def qgisserver_base_url(project: str, psql_schema: str) -> str:
    url = f"{config().qgisserver_url}"
    if StorageBackend.type() == StorageBackend.FILESYSTEM:
        url = f"{url}/{project}?"
    elif StorageBackend.type() == StorageBackend.POSTGRESQL:
        #service = config().qgisserver_projects_psql_service
        #url = f"{url}?MAP=postgresql:?service={service}%26schema={psql_schema}%26project={project}&"
        dbname = config().qgisserver_projects_psql_dbname
        user = config().qgisserver_projects_psql_user
        password = config().qgisserver_projects_psql_password
        host = config().qgisserver_projects_psql_host
        port = config().qgisserver_projects_psql_port
        url = f"{url}?MAP=postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode=disable&schema=public&project={project}"
    return url


# see boto3 doc
class ProgressPercentage:

    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self._last = 0

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100

            if percentage < self._last + 5:
                return

            self._last = percentage

            if QSAConfig().loglevel == logging.DEBUG:
                print(
                    "\r%s  %s / %s  (%.2f%%)"
                    % (
                        self._filename,
                        self._seen_so_far,
                        self._size,
                        percentage,
                    ),
                    file=sys.stderr,
                )
            sys.stdout.flush()


def s3_bucket_upload(bucket: str, source: str, dest: str) -> (bool, str):

    size = float(os.path.getsize(source) >> 20)

    logger().debug(
        f"[utils.s3_bucket_upload] Upload {source} ({size}MB) to S3 bucket {bucket} in {dest}"
    )

    try:
        s3 = boto3.resource("s3")
        s3.Bucket(bucket).upload_file(
            source,
            dest,
            Callback=ProgressPercentage(source),
        )
    except ClientError as e:
        return False, "Upload to S3 bucket failed"

    return True, ""
