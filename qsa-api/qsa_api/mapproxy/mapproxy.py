# coding: utf8

import sys
import os
import yaml
import boto3
import shutil
from pathlib import Path

from qgis.PyQt.QtCore import Qt, QDateTime

from ..utils import config, logger, qgisserver_base_url


class QSAMapProxy:
    def __init__(self, name: str, schema: str = "") -> None:
        self.name = name
        self.schema = "public"
        if schema:
            self.schema = schema

    def create(self) -> None:
        parent = Path(__file__).resolve().parent
        template = parent / "mapproxy.yaml"
        shutil.copy(template, self._mapproxy_project)

    def remove(self) -> None:
        self._mapproxy_project.unlink()

    def write(self) -> None:
        with open(self._mapproxy_project, "w") as file:
            yaml.safe_dump(self.cfg, file, sort_keys=False)

    def read(self) -> (bool, str):
        # if a QGIS project is created manually without QSA, the MapProxy
        # configuration file may not be created at this point.
        if not self._mapproxy_project.exists():
            self.create()

        try:
            with open(self._mapproxy_project, "r") as file:
                self.cfg = yaml.safe_load(file)
        except yaml.scanner.ScannerError as e:
            return (
                False,
                f"Failed to load MapProxy configuration file {self._mapproxy_project}",
            )

        if self.cfg is None:
            return (
                False,
                f"Failed to load MapProxy configuration file {self._mapproxy_project}",
            )

        return True, ""

    def metadata(self) -> dict:
        md = {}

        md["storage"] = ""
        md["valid"] = False

        if self._mapproxy_project.exists():
            md["valid"] = True

            md["storage"] = "filesystem"
            if config().mapproxy_cache_s3_bucket:
                md["storage"] = "s3"

        return md

    def clear_cache(self, layer_name: str) -> None:
        if config().mapproxy_cache_s3_bucket:
            bucket_name = config().mapproxy_cache_s3_bucket
            cache_dir = f"{config().mapproxy_cache_s3_dir}/{layer_name}"
            if cache_dir[0] == "/":
                cache_dir = cache_dir[1:]
            self.debug(f"Clear S3 cache 's3://{bucket_name}/{cache_dir}'")
            s3 = boto3.resource(
                "s3",
                aws_access_key_id=config().aws_access_key_id,
                aws_secret_access_key=config().aws_secret_access_key,
            )
            bucket = s3.Bucket(bucket_name)
            bucket.objects.filter(Prefix=cache_dir).delete()
        else:
            cache_dir = self._mapproxy_project.parent / "cache_data"
            self.debug(f"Clear tiles cache '{cache_dir}'")
            
            for d in cache_dir.glob(f"{layer_name}_cache_*"):
                self.debug(f"Test cache  '{d}'")
                for root, dirs, files in os.walk(d, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(d)

            self.debug(f"End tiles cache '{cache_dir}'")
            # cache_dir = self._mapproxy_project.parent / "cache_data" / "legends"
            # self.debug(f"Clear legends cache '{cache_dir}'")
            # shutil.rmtree(cache_dir, ignore_errors=True)

    def add_layer(
        self,
        name: str,
        bbox: list,
        srs: int,
        is_raster: bool,
        datetime: QDateTime | None,
    ) -> (bool, str):
        if self.cfg is None:
            return False, "Invalid MapProxy configuration"

        if "layers" not in self.cfg:
            self.cfg["layers"] = []
            self.cfg["caches"] = {}
            self.cfg["sources"] = {}

        lyr = {"name": name, "title": name, "sources": [f"{name}_cache"]}
        if datetime and is_raster:
            lyr["dimensions"] = {}
            lyr["dimensions"]["time"] = {
                "values": [datetime.toString(Qt.ISODate)]
            }

        self.cfg["layers"].append(lyr)

        c = {"grids": ["webmercator"], "sources": [f"{name}_wms"]}
        if is_raster:
            c["use_direct_from_level"] = 14
            c["meta_size"] = [1, 1]
            c["meta_buffer"] = 0

        if config().mapproxy_cache_s3_bucket:
            s3_cache_dir = f"{config().mapproxy_cache_s3_dir}/{name}"
            c["cache"] = {}
            c["cache"]["type"] = "s3"
            c["cache"]["directory"] = s3_cache_dir
            c["cache"]["bucket_name"] = config().mapproxy_cache_s3_bucket

        self.cfg["caches"][f"{name}_cache"] = c

        s = {
            "type": "wms",
            "wms_opts": {
                "legendgraphic": True,
            },
            "req": {
                "url": qgisserver_base_url(self.name, self.schema),
                "layers": name,
                "transparent": True,
            },
            "coverage": {"bbox": bbox, "srs": f"EPSG:{srs}"},
        }
        if datetime and is_raster:
            s["forward_req_params"] = ["TIME"]

        self.cfg["sources"][f"{name}_wms"] = s

        return True, ""

    def remove_layer(self, name: str) -> None:
        # early return
        if "layers" not in self.cfg:
            return

        # clear cache
        self.clear_cache(name)

        # clean layers
        layers = []
        for layer in self.cfg["layers"]:
            if layer["name"] != name:
                layers.append(layer)
        self.cfg["layers"] = layers

        # clean caches
        cache_name = f"{name}_cache"
        if cache_name in self.cfg["caches"]:
            self.cfg["caches"].pop(cache_name)

        # clean sources
        source_name = f"{name}_wms"
        if source_name in self.cfg["sources"]:
            self.cfg["sources"].pop(source_name)

    def debug(self, msg: str) -> None:
        caller = f"{self.__class__.__name__}.{sys._getframe().f_back.f_code.co_name}"
        msg = f"[{caller}][{self.name}] {msg}"
        logger().debug(msg)

    @staticmethod
    def _mapproxy_projects_dir() -> Path:
        return Path(config().mapproxy_projects_dir)

    @property
    def _mapproxy_project(self) -> Path:
        return QSAMapProxy._mapproxy_projects_dir() / f"{self.name}.yaml"
