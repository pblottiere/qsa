# coding: utf8

import shutil
import sqlite3
from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.core import (
    Qgis,
    QgsSymbol,
    QgsProject,
    QgsMapLayer,
    QgsWkbTypes,
    QgsFillSymbol,
    QgsLineSymbol,
    QgsApplication,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsMarkerSymbol,
    QgsFeatureRenderer,
    QgsReadWriteContext,
    QgsRasterMinMaxOrigin,
    QgsContrastEnhancement,
    QgsSingleSymbolRenderer,
    QgsSimpleFillSymbolLayer,
    QgsSimpleLineSymbolLayer,
    QgsSimpleMarkerSymbolLayer,
)
from qgis.PyQt.QtXml import QDomDocument, QDomNode

from .mapproxy import QSAMapProxy
from .utils import RasterSymbologyRenderer, StorageBackend, config


RENDERER_TAG_NAME = "renderer-v2"  # constant from core/symbology/renderer.h


class QSAProject:
    def __init__(self, name: str, schema: str = "public") -> None:
        self.name: str = name
        self.schema: str = "public"
        if schema:
            self.schema = schema

    @property
    def sqlite_db(self) -> Path:
        p = self._qgis_project_dir / "qsa.db"
        if not p.exists():
            con = sqlite3.connect(p)
            cur = con.cursor()
            cur.execute("CREATE TABLE styles_default(geometry, style)")
            cur.execute("INSERT INTO styles_default VALUES('line', 'default')")
            cur.execute(
                "INSERT INTO styles_default VALUES('polygon', 'default')"
            )
            cur.execute(
                "INSERT INTO styles_default VALUES('point', 'default')"
            )
            con.commit()
            con.close()
        return p

    @staticmethod
    def projects(schema: str = "") -> list:
        p = []

        if StorageBackend.type() == StorageBackend.FILESYSTEM:
            for i in QSAProject._qgis_projects_dir().glob("**/*.qgs"):
                name = i.parent.name.replace(
                    QSAProject._qgis_project_dir_prefix(), ""
                )
                p.append(QSAProject(name))
        else:
            service = config().qgisserver_projects_psql_service
            uri = f"postgresql:?service={service}&schema={schema}"

            storage = (
                QgsApplication.instance()
                .projectStorageRegistry()
                .projectStorageFromType("postgresql")
            )
            for pname in storage.listProjects(uri):
                p.append(QSAProject(pname, schema))

        return p

    @property
    def styles(self) -> list[str]:
        s = []
        for qml in self._qgis_project_dir.glob("**/*.qml"):
            s.append(qml.stem)
        return s

    @property
    def project(self) -> QgsProject:
        project = QgsProject()
        project.read(self._qgis_project_uri)
        return project

    @property
    def layers(self) -> list:
        layers = []
        p = self.project
        for layer in p.mapLayers().values():
            layers.append(layer.name())
        return layers

    @property
    def metadata(self) -> dict:
        m = {}
        p = self.project
        m["author"] = p.metadata().author()
        m["creation_datetime"] = (
            p.metadata().creationDateTime().toString(Qt.ISODate)
        )
        m["crs"] = p.crs().authid()
        m["storage"] = StorageBackend.type().name.lower()

        if StorageBackend.type() == StorageBackend.POSTGRESQL:
            m["schema"] = self.schema
        return m

    def style_default(self, geometry: str) -> bool:
        con = sqlite3.connect(self.sqlite_db.as_posix())
        cur = con.cursor()
        sql = f"SELECT style FROM styles_default WHERE geometry = '{geometry}'"
        res = cur.execute(sql)
        default_style = res.fetchone()[0]
        con.close()
        return default_style

    def style(self, name: str) -> dict:
        if name not in self.styles:
            return {}

        path = self._qgis_project_dir / f"{name}.qml"
        doc = QDomDocument()
        doc.setContent(open(path.as_posix()).read())
        node = QDomNode(doc.firstChild())

        renderer_node = node.firstChildElement(RENDERER_TAG_NAME)
        renderer = QgsFeatureRenderer.load(
            renderer_node, QgsReadWriteContext()
        )
        symbol = renderer.symbol()
        props = symbol.symbolLayer(0).properties()

        geom = "line"
        symbol = QgsSymbol.symbolTypeToString(symbol.type()).lower()
        if symbol == "fill":
            geom = "polygon"

        m = {}
        m["symbology"] = "single_symbol"
        m["name"] = name
        m["symbol"] = symbol
        m["geometry"] = geom
        m["properties"] = props

        return m

    def style_update(self, geometry: str, style: str) -> None:
        con = sqlite3.connect(self.sqlite_db.as_posix())
        cur = con.cursor()
        sql = f"UPDATE styles_default SET style = '{style}' WHERE geometry = '{geometry}'"
        cur.execute(sql)
        con.commit()
        con.close()

    def default_styles(self) -> list:
        s = {}

        s["polygon"] = self.style_default("polygon")
        s["line"] = self.style_default("line")
        s["point"] = self.style_default("point")

        return s

    def layer(self, name: str) -> dict:
        project = QgsProject()
        project.read(self._qgis_project_uri)
        layers = project.mapLayersByName(name)
        if layers:
            layer = layers[0]

            infos = {}
            infos["valid"] = layer.isValid()
            infos["name"] = layer.name()
            infos["type"] = layer.type().name.lower()

            if layer.type() == Qgis.LayerType.Vector:
                infos["geometry"] = QgsWkbTypes.displayString(layer.wkbType())

            infos["source"] = layer.source()
            infos["crs"] = layer.crs().authid()
            infos["current_style"] = layer.styleManager().currentStyle()
            infos["styles"] = layer.styleManager().styles()
            infos["bbox"] = layer.extent().asWktCoordinates()
            return infos
        return {}

    def layer_update_style(
        self, layer_name: str, style_name: str, current: bool
    ) -> (bool, str):
        if layer_name not in self.layers:
            return False, f"Layer '{layer_name}' does not exist"

        if style_name != "default" and style_name not in self.styles:
            return False, f"Style '{style_name}' does not exist"

        project = QgsProject()
        project.read(self._qgis_project_uri)

        style_path = self._qgis_project_dir / f"{style_name}.qml"

        layer = project.mapLayersByName(layer_name)[0]

        if style_name not in layer.styleManager().styles():
            l = layer.clone()
            l.loadNamedStyle(style_path.as_posix())  # set "default" style

            layer.styleManager().addStyle(
                style_name, l.styleManager().style("default")
            )

        import sys

        print("layer_update_style 0", file=sys.stderr)
        if current:
            print("layer_update_style 1", file=sys.stderr)
            layer.styleManager().setCurrentStyle(style_name)

            # refresh min/max for the current layer if necessary
            # (because the style is built on an empty geotiff)
            if layer.type() == QgsMapLayer.RasterLayer:
                print("layer_update_style 2", file=sys.stderr)
                renderer = RasterSymbologyRenderer(layer.renderer().type())
                renderer.refresh_min_max(layer)

            if self._mapproxy_enabled:
                mp = QSAMapProxy(self.name)
                mp.clear_cache(layer_name)

        project.write()

        return True, ""

    def layer_exists(self, name: str) -> bool:
        return bool(self.layer(name))

    def remove_layer(self, name: str) -> None:
        # remove layer in qgis project
        project = QgsProject()
        project.read(self._qgis_project_uri)

        ids = []
        for layer in project.mapLayersByName(name):
            ids.append(layer.id())
        project.removeMapLayers(ids)

        rc = project.write()

        # remove layer in mapproxy config
        if self._mapproxy_enabled:
            mp = QSAMapProxy(self.name)
            mp.read()
            mp.remove_layer(name)
            mp.write()

        return rc

    def exists(self) -> bool:
        if StorageBackend.type() == StorageBackend.FILESYSTEM:
            return self._qgis_project_dir.exists()
        else:
            service = config().qgisserver_projects_psql_service
            uri = f"postgresql:?service={service}&schema={self.schema}"

            storage = (
                QgsApplication.instance()
                .projectStorageRegistry()
                .projectStorageFromType("postgresql")
            )
            projects = storage.listProjects(uri)

            return self.name in projects and self._qgis_projects_dir().exists()

    def create(self, author: str) -> bool:
        if self.exists():
            return False

        # create qgis directory for qsa sqlite database and .qgs file if
        # filesystem storage based
        self._qgis_project_dir.mkdir(parents=True, exist_ok=True)

        # create qgis project
        project = QgsProject()
        m = project.metadata()
        m.setAuthor(author)
        project.setMetadata(m)
        rc = project.write(self._qgis_project_uri)

        # create mapproxy config file
        if self._mapproxy_enabled:
            mp = QSAMapProxy(self.name)
            mp.create()

        # init sqlite database
        self.sqlite_db

        return rc

    def remove(self) -> None:
        shutil.rmtree(self._qgis_project_dir)

        if StorageBackend.type() == StorageBackend.POSTGRESQL:
            storage = (
                QgsApplication.instance()
                .projectStorageRegistry()
                .projectStorageFromType("postgresql")
            )
            storage.removeProject(self._qgis_project_uri)

        if self._mapproxy_enabled:
            QSAMapProxy(self.name).remove()

    def add_layer(
        self, datasource: str, layer_type: str, name: str, epsg_code: int
    ) -> (bool, str):
        t = self._layer_type(layer_type)
        if t is None:
            return False, "Invalid layer type"

        lyr = None
        if t == Qgis.LayerType.Vector:
            lyr = QgsVectorLayer(datasource, name, "ogr")
        elif t == Qgis.LayerType.Raster:
            lyr = QgsRasterLayer(datasource, name, "gdal")
        else:
            return False, "Invalid layer type"

        crs = lyr.crs()
        crs.createFromString(f"EPSG:{epsg_code}")
        lyr.setCrs(crs)

        if not lyr.isValid():
            return False, "Invalid layer"

        # create project
        project = QgsProject()
        project.read(self._qgis_project_uri)

        project.addMapLayer(lyr)
        project.setCrs(crs)
        project.write()

        # set default style
        if t == Qgis.LayerType.Vector:
            geometry = lyr.geometryType().name.lower()
            default_style = self.style_default(geometry)

            self.layer_update_style(name, default_style, True)

        # add layer in mapproxy config file
        bbox = list(
            map(
                float,
                lyr.extent().asWktCoordinates().replace(",", "").split(" "),
            )
        )

        if self._mapproxy_enabled:
            mp = QSAMapProxy(self.name)
            mp.read()
            mp.add_layer(name, bbox, epsg_code)
            mp.write()

        return True, ""

    def add_style(
        self,
        name: str,
        layer_type: str,
        symbology: dict,
        rendering: dict,
    ) -> (bool, str):
        t = self._layer_type(layer_type)

        if t == Qgis.LayerType.Vector:
            return self._add_style_vector(name, symbology, rendering)
        elif t == Qgis.LayerType.Raster:
            return self._add_style_raster(name, symbology, rendering)
        elif t is None:
            return False, "Invalid layer type"

    def _add_style_raster(
        self, name: str, symbology: dict, rendering: dict
    ) -> (bool, str):
        # safety check
        if "type" not in symbology:
            return False, "`type` is missing in `symbology`"

        if "properties" not in symbology:
            return False, "`properties` is missing in `symbology`"

        # init renderer
        tif = Path(__file__).resolve().parent / "empty.tif"
        rl = QgsRasterLayer(tif.as_posix(), "", "gdal")

        # symbology
        renderer = RasterSymbologyRenderer(symbology["type"])
        renderer.load(symbology["properties"])

        # config rendering
        if "gamma" in rendering:
            rl.brightnessFilter().setGamma(float(rendering["gamma"]))

        if "brightness" in rendering:
            rl.brightnessFilter().setBrightness(int(rendering["brightness"]))

        if "contrast" in rendering:
            rl.brightnessFilter().setContrast(int(rendering["contrast"]))

        if "saturation" in rendering:
            rl.hueSaturationFilter().setSaturation(
                int(rendering["saturation"])
            )

        # save style
        if renderer.renderer:
            rl.setRenderer(renderer.renderer)

            # contrast enhancement needs to be managed after setting renderer
            if renderer.contrast_algorithm:
                rl.setContrastEnhancement(
                    renderer.contrast_algorithm, renderer.contrast_limits
                )

                # user defined min/max
                if (
                    renderer.contrast_limits
                    == QgsRasterMinMaxOrigin.Limits.None_
                ):
                    if (
                        renderer.type
                        == RasterSymbologyRenderer.Type.SINGLE_BAND_GRAY
                    ):
                        ce = QgsContrastEnhancement(
                            rl.renderer().contrastEnhancement()
                        )
                        if renderer.gray_min is not None:
                            ce.setMinimumValue(renderer.gray_min)
                        if renderer.gray_max is not None:
                            ce.setMaximumValue(renderer.gray_max)
                        rl.renderer().setContrastEnhancement(ce)
                    elif (
                        renderer.type
                        == RasterSymbologyRenderer.Type.MULTI_BAND_COLOR
                    ):
                        # red
                        red_ce = QgsContrastEnhancement(
                            rl.renderer().redContrastEnhancement()
                        )
                        if renderer.red_min is not None:
                            red_ce.setMinimumValue(renderer.red_min)
                        if renderer.red_max is not None:
                            red_ce.setMaximumValue(renderer.red_max)
                        rl.renderer().setRedContrastEnhancement(red_ce)

                        # green
                        green_ce = QgsContrastEnhancement(
                            rl.renderer().greenContrastEnhancement()
                        )
                        if renderer.green_min is not None:
                            green_ce.setMinimumValue(renderer.green_min)
                        if renderer.green_max is not None:
                            green_ce.setMaximumValue(renderer.green_max)
                        rl.renderer().setGreenContrastEnhancement(green_ce)

                        # blue
                        blue_ce = QgsContrastEnhancement(
                            rl.renderer().blueContrastEnhancement()
                        )
                        if renderer.blue_min is not None:
                            blue_ce.setMinimumValue(renderer.blue_min)
                        if renderer.blue_max is not None:
                            blue_ce.setMaximumValue(renderer.blue_max)
                        rl.renderer().setBlueContrastEnhancement(blue_ce)

            # save
            path = self._qgis_project_dir / f"{name}.qml"
            rl.saveNamedStyle(
                path.as_posix(), categories=QgsMapLayer.AllStyleCategories
            )
            return True, ""

        return False, "Error"

    def _add_style_vector(
        self, name: str, symbology: dict, rendering: dict
    ) -> (bool, str):
        if "type" not in symbology:
            return False, "`type` is missing in `symbology`"

        if "symbol" not in symbology:
            return False, "`symbol` is missing in `symbology`"

        if "properties" not in symbology:
            return False, "`properties` is missing in `symbology`"

        if symbology["type"] != "single_symbol":
            return False, "Invalid symbol"

        r = None
        vl = QgsVectorLayer()
        symbol = symbology["symbol"]
        properties = symbology["properties"]

        if symbol == "line":
            r = QgsSingleSymbolRenderer(
                QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
            )

            props = QgsSimpleLineSymbolLayer().properties()
            for key in properties.keys():
                if key not in props:
                    return False, "Invalid properties"

            symbol = QgsLineSymbol.createSimple(properties)
            r.setSymbol(symbol)
        elif symbol == "fill":
            r = QgsSingleSymbolRenderer(
                QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
            )

            props = QgsSimpleFillSymbolLayer().properties()
            for key in properties.keys():
                if key not in props:
                    return False, "Invalid properties"

            symbol = QgsFillSymbol.createSimple(properties)
            r.setSymbol(symbol)
        elif symbol == "marker":
            r = QgsSingleSymbolRenderer(
                QgsSymbol.defaultSymbol(QgsWkbTypes.PointGeometry)
            )

            props = QgsSimpleMarkerSymbolLayer().properties()
            for key in properties.keys():
                if key not in props:
                    return False, "Invalid properties"

            symbol = QgsMarkerSymbol.createSimple(properties)
            r.setSymbol(symbol)

        if "opacity" in rendering:
            vl.setOpacity(float(rendering["opacity"]))

        if r:
            vl.setRenderer(r)

            path = self._qgis_project_dir / f"{name}.qml"
            vl.saveNamedStyle(
                path.as_posix(), categories=QgsMapLayer.Symbology
            )
            return True, ""

        return False, "Error"

    def remove_style(self, name: str) -> bool:
        if name not in self.styles:
            return False, f"Style '{name}' does not exist"

        p = self.project
        for layer in p.mapLayers().values():
            if name == layer.styleManager().currentStyle():
                return False, f"Style is used by {layer.name()}"

        for layer in p.mapLayers().values():
            layer.styleManager().removeStyle(name)

        path = self._qgis_project_dir / f"{name}.qml"
        path.unlink()

        p.write()

        return True, ""

    @staticmethod
    def _qgis_projects_dir() -> Path:
        return Path(config().qgisserver_projects_dir)

    @staticmethod
    def _layer_type(layer_type: str) -> Qgis.LayerType | None:
        if layer_type.lower() == "vector":
            return Qgis.LayerType.Vector
        elif layer_type.lower() == "raster":
            return Qgis.LayerType.Raster
        return None

    @property
    def _mapproxy_enabled(self) -> bool:
        return bool(config().mapproxy_projects_dir)

    @property
    def _qgis_project_dir(self) -> Path:
        return (
            self._qgis_projects_dir()
            / f"{QSAProject._qgis_project_dir_prefix(self.schema)}{self.name}"
        )

    @staticmethod
    def _qgis_project_dir_prefix(schema: str = "") -> str:
        prefix = ""
        if StorageBackend.type() == StorageBackend.POSTGRESQL:
            prefix = f"{schema}_"
        return prefix

    @property
    def _qgis_project_uri(self) -> str:
        if StorageBackend.type() == StorageBackend.POSTGRESQL:
            service = config().qgisserver_projects_psql_service
            return f"postgresql:?service={service}&schema={self.schema}&project={self.name}"
        else:
            return (self._qgis_project_dir / f"{self.name}.qgs").as_posix()
