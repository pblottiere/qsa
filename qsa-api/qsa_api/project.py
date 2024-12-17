# coding: utf8

import sys
import shutil
import threading
import sqlite3
from pathlib import Path
from flask import current_app

from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt, QDateTime
from qgis.core import (
    Qgis,
    QgsSymbol,
    QgsProject,
    QgsSettings,
    QgsWkbTypes,
    QgsMapLayer,
    QgsUnitTypes,
    QgsFillSymbol,
    QgsLineSymbol,
    QgsApplication,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsEffectStack,
    QgsMarkerSymbol,
    QgsDateTimeRange,
    QgsRendererRange,
    QgsDropShadowEffect,
    QgsDrawSourceEffect,
    QgsRendererCategory,
    QgsRasterMinMaxOrigin,
    QgsContrastEnhancement,
    QgsSvgMarkerSymbolLayer,
    QgsSingleSymbolRenderer,
    QgsSimpleFillSymbolLayer,
    QgsSimpleLineSymbolLayer,
    QgsSimpleMarkerSymbolLayer,
    QgsGraduatedSymbolRenderer,
    QgsCategorizedSymbolRenderer,
    QgsRasterLayerTemporalProperties,
)

from .mapproxy import QSAMapProxy
from .vector import VectorSymbologyRenderer
from .utils import StorageBackend, config, logger
from .raster import RasterSymbologyRenderer, RasterOverview


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
            p.parent.mkdir(parents=True, exist_ok=True)
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
        self.debug(f"{len(s)} styles found")
        return s

    @property
    def project(self) -> QgsProject:
        project = QgsProject()
        project.read(self._qgis_project_uri, Qgis.ProjectReadFlag.DontResolveLayers)
        return project

    @property
    def layers(self) -> list:
        layers = []

        p = QgsProject()
        p.read(self._qgis_project_uri, Qgis.ProjectReadFlag.DontResolveLayers)

        for layer in p.mapLayers().values():
            layers.append(layer.name())
        self.debug(f"{len(layers)} layers found")
        return layers

    @property
    def metadata(self) -> dict:
        m = {}

        p = QgsProject()
        p.read(self._qgis_project_uri, Qgis.ProjectReadFlag.DontResolveLayers)

        m["author"] = p.metadata().author()
        m["creation_datetime"] = (
            p.metadata().creationDateTime().toString(Qt.ISODate)
        )
        m["crs"] = p.crs().authid()
        m["storage"] = StorageBackend.type().name.lower()

        if StorageBackend.type() == StorageBackend.POSTGRESQL:
            m["schema"] = self.schema

        m["cache"] = "disabled"
        if self._mapproxy_enabled:
            m["cache"] = "mapproxy"

        return m

    def cache_metadata(self) -> (dict, str):
        if self._mapproxy_enabled:
            return QSAMapProxy(self.name).metadata(), ""
        return {}, "Cache is disabled"

    def cache_reset(self) -> (bool, str):
        if self._mapproxy_enabled:
            mp = QSAMapProxy(self.name)
            rc, err = mp.read()
            if not rc:
                return False, err

            p = QgsProject()
            p.read(self._qgis_project_uri)

            for layer in p.mapLayers().values():
                t = layer.type()
                bbox = QSAProject._layer_bbox(layer)
                epsg_code = QSAProject._layer_epsg_code(layer)

                mp.remove_layer(layer.name())
                mp.add_layer(
                    layer.name(), bbox, epsg_code, t == Qgis.LayerType.Raster, None
                )

                mp.write()

            return True, ""

        return False, "Cache is disabled"

    def style_default(self, geometry: str) -> bool:
        con = sqlite3.connect(self.sqlite_db.as_posix())
        cur = con.cursor()
        sql = f"SELECT style FROM styles_default WHERE geometry = '{geometry}'"
        res = cur.execute(sql)
        default_style = res.fetchone()[0]
        con.close()
        return default_style

    def style(self, name: str) -> (dict, str):
        if name not in self.styles:
            return {}, "Invalid style"

        path = self._qgis_project_dir / f"{name}.qml"

        if VectorSymbologyRenderer.style_is_vector(path):
            return VectorSymbologyRenderer.style_to_json(path)
        else:
            return RasterSymbologyRenderer.style_to_json(path)

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
        flags = Qgis.ProjectReadFlags()
        flags |= Qgis.ProjectReadFlag.ForceReadOnlyLayers
        project = QgsProject()
        project.read(self._qgis_project_uri,flags)

        layers = project.mapLayersByName(name)
        if layers:
            layer = layers[0]

            infos = {}
            infos["name"] = layer.name()
            infos["type"] = layer.type().name.lower()

            if layer.type() == Qgis.LayerType.Vector:
                infos["geometry"] = QgsWkbTypes.displayString(layer.wkbType())
            elif layer.type() == Qgis.LayerType.Raster:
                infos["bands"] = layer.bandCount()
                infos["data_type"] = layer.dataProvider().dataType(1).name.lower()

            infos["source"] = layer.source()
            infos["crs"] = layer.crs().authid()
            infos["current_style"] = layer.styleManager().currentStyle()
            infos["styles"] = layer.styleManager().styles()
            infos["valid"] = layer.isValid()
            infos["bbox"] = layer.extent().asWktCoordinates()

            return infos
        return {}

    def layer_update_style(
        self, layer_name: str, style_name: str, current: bool
    ) -> (bool, str):
        # if layer_name not in self.layers:
        #     return False, f"Layer '{layer_name}' does not exist"

        # if style_name != "default" and style_name not in self.styles:
        #     return False, f"Style '{style_name}' does not exist"

                
        self.debug("Start thread for clearing MapProxy cache")
        mp = QSAMapProxy(self.name)
        mp.clear_cache(layer_name)
        
        self.debug("cache_thread is running")
        QgsSettings().setValue("qgis/validate_layers", False)
        QgsSettings().setValue("qgis/disableGetPrint", True)
        
        QgsSettings().setValue("qgis/enable_labeling", False)
        QgsSettings().setValue("qgis/enable_advanced_editing", False)
        QgsSettings().setValue("qgis/disableGetPrint", True)
        QgsSettings().setValue("qgis/disable_layouts", True)
        QgsSettings().setValue("qgis/ignore_crs_transforms", True)
        QgsSettings().setValue("qgis/skipWMSConnections", True)
        QgsSettings().setValue("qgis/enable_rendering_cache", False)
        QgsSettings().setValue("qgis/enable_onscreen_rendering", False)
        
        flags = Qgis.ProjectReadFlags()
        #flags |= Qgis.ProjectReadFlag.ForceReadOnlyLayers
        flags |= Qgis.ProjectReadFlag.FlagDontLoadLayouts
        flags |= Qgis.ProjectReadFlag.FlagTrustLayerMetadata
        flags |= Qgis.ProjectReadFlag.FlagDontLoad3DViews

        project = QgsProject()
        project.read(self._qgis_project_uri, flags)

        self.debug("project.read")
        style_path = self._qgis_project_dir / f"{style_name}.qml"
        layer = project.mapLayersByName(layer_name)[0]

        self.debug("project.mapLayersByName")
        if style_name not in layer.styleManager().styles():
            self.debug(f"Add new style {style_name} in style manager")
            l = layer.clone()
            l.loadNamedStyle(style_path.as_posix())  # set "default" style

            layer.styleManager().addStyle(
                style_name, l.styleManager().style("default")
            )

        if current:
            self.debug(f"Set default style {style_name}")
            layer.styleManager().setCurrentStyle(style_name)

            # refresh min/max for the current layer if necessary
            # (because the style is built on an empty geotiff)
            if layer.type() == QgsMapLayer.RasterLayer:
                self.debug("Refresh symbology renderer min/max")
                renderer = RasterSymbologyRenderer(layer.renderer().type())
                renderer.refresh_min_max(layer)

        self.debug("Write project")
        project.write()

        return True, ""

    def layer_exists(self, name: str) -> bool:
        return bool(self.layer(name))

    def remove_layer(self, name: str) -> bool:
        # remove layer in qgis project
        project = QgsProject()
        project.read(self._qgis_project_uri, Qgis.ProjectReadFlag.DontResolveLayers)

        ids = []
        for layer in project.mapLayersByName(name):
            ids.append(layer.id())
        project.removeMapLayers(ids)

        rc = project.write()

        # remove layer in mapproxy config
        if self._mapproxy_enabled:
            mp = QSAMapProxy(self.name)
            rc, err = mp.read()
            if not rc:
                self.debug(err)
                return False

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

            # necessary step if the project has been created without QSA
            if self.name in projects:
                self._qgis_projects_dir().mkdir(parents=True, exist_ok=True)

            return self.name in projects and self._qgis_projects_dir().exists()

    def create(self, author: str) -> (bool, str):
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

        crs = project.crs()
        crs.createFromString("EPSG:3857")  # default to webmercator
        project.setCrs(crs)

        self.debug("Write QGIS project")
        rc = project.write(self._qgis_project_uri)

        # create mapproxy config file
        if self._mapproxy_enabled:
            self.debug("Write MapProxy configuration file")
            mp = QSAMapProxy(self.name)
            mp.create()

        # init sqlite database
        self.sqlite_db

        return rc, project.error()

    def remove(self) -> None:
        # clear cache and stuff
        for layer in self.layers:
            self.remove_layer(layer)

        # remove mapproxy config file
        if self._mapproxy_enabled:
            mp = QSAMapProxy(self.name)
            mp.remove()

        # remove qsa projects dir
        shutil.rmtree(self._qgis_project_dir, ignore_errors=True)

        # remove remove qgis prohect in db if necessary
        if StorageBackend.type() == StorageBackend.POSTGRESQL:
            storage = (
                QgsApplication.instance()
                .projectStorageRegistry()
                .projectStorageFromType("postgresql")
            )
            storage.removeProject(self._qgis_project_uri)

    def add_layer(
        self,
        datasource: str,
        layer_type: str,
        name: str,
        epsg_code: int,
        overview: bool,
        datetime: QDateTime | None,
    ) -> (bool, str):
        t = self._layer_type(layer_type)
        if t is None:
            return False, "Invalid layer type"

        if name in self.layers:
            return False, f"A layer {name} already exists"

        provider = QSAProject._layer_provider(t, datasource)

        lyr = None
        if t == Qgis.LayerType.Vector:
            self.debug("Init vector layer")
            lyr = QgsVectorLayer(datasource, name, provider)
        elif t == Qgis.LayerType.Raster:
            self.debug("Init raster layer")
            lyr = QgsRasterLayer(datasource, name, provider)

            ovr = RasterOverview(lyr)
            if overview:
                if not ovr.is_valid():
                    self.debug("Build overviews")
                    rc, err = ovr.build()
                    if not rc:
                        return False, err
                else:
                    self.debug("Overviews already exist")

            if datetime:
                self.debug("Activate temporal properties")
                mode = QgsRasterLayerTemporalProperties.ModeFixedTemporalRange
                props = lyr.temporalProperties()
                props.setMode(mode)
                dt_range = QgsDateTimeRange(datetime, datetime)
                props.setFixedTemporalRange(dt_range)
                props.setIsActive(True)
        else:
            return False, "Invalid layer type"

        if lyr is None:
            return False, "Invalid layer (None)"

        if not lyr.isValid():
            return False, f"Invalid layer ({lyr.error()})"

        if epsg_code > 0:
            crs = lyr.crs()
            crs.createFromString(f"EPSG:{epsg_code}")
            lyr.setCrs(crs)

        if not lyr.isValid():
            return False, f"Invalid layer ({lyr.error()})"

        # create project
        project = QgsProject()
        project.read(self._qgis_project_uri, Qgis.ProjectReadFlag.DontResolveLayers)
        project.addMapLayer(lyr)

        self.debug("Write QGIS project")
        project.write()

        # set default style
        if t == Qgis.LayerType.Vector:
            self.debug("Set default style")
            geometry = lyr.geometryType().name.lower()
            default_style = self.style_default(geometry)

            self.layer_update_style(name, default_style, True)

        # add layer in mapproxy config file
        if self._mapproxy_enabled:
            self.debug("Update MapProxy configuration file")

            bbox = QSAProject._layer_bbox(lyr)
            epsg_code = QSAProject._layer_epsg_code(lyr)
            if epsg_code < 0:
                return False, f"Invalid CRS {lyr.crs().authid()}"

            self.debug(f"EPSG code {epsg_code}")

            mp = QSAMapProxy(self.name)
            rc, err = mp.read()
            if not rc:
                return False, err

            rc, err = mp.add_layer(
                name, bbox, epsg_code, t == Qgis.LayerType.Raster, datetime
            )
            if not rc:
                return False, err

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
        match t :
            case Qgis.LayerType.Vector:
                return self._add_style_vector(name, symbology, rendering)
            case  Qgis.LayerType.Raster:
                return self._add_style_raster(name, symbology, rendering)
            case other:
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
        tif = Path(__file__).resolve().parent / "raster" / "empty.tif"
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
        

        render = None
        vl = QgsVectorLayer()
        
        match symbology["type"] : 
            case "single_symbol": 
                render = self._create_single_symbol_style(symbology)
            case "graduated": 
                render = self._create_graduated_style(symbology)
            case "categorized": 
                render = self._create_categorized_style(symbology)

        
        if "opacity" in rendering:
            vl.setOpacity(float(rendering["opacity"]))

        if render:
            vl.setRenderer(render)

            path = self._qgis_project_dir / f"{name}.qml"
            vl.saveNamedStyle(
                path.as_posix(), categories=vl.Symbology
            )
            return True, ""

        return False, "Error"
    
    def _create_categorized_style(self,symbology: dict) -> QgsCategorizedSymbolRenderer:
        symbol = symbology["symbol"] 
        properties = symbology["properties"]
        attribut = properties["attributs"]
        ranges = []
        
        match symbol:
            case "fill":
                for categorized_value in properties["list_categorized"]:
                    properties = {
                        "outline_width" : categorized_value["outline_width"],
                        "outline_style" : categorized_value["outline_style"],
                        "outline_color" : categorized_value["outline_color"],
                    }
                    symbol = QgsFillSymbol.createSimple(properties)
                    symbol.setColor(QColor(categorized_value["color"]))

                    range = QgsRendererCategory(categorized_value["value"], symbol, "test")
                    ranges.append(range)
                
            case "line":  
                for categorized_value in properties["list_categorized"]:
                    properties = {
                        "outline_width" : categorized_value["outline_width"],
                        "outline_style" : categorized_value["outline_style"],
                    }
                    symbol = QgsLineSymbol.createSimple(properties)
                    symbol.setColor(QColor(categorized_value["outline_color"]))

                    range = QgsRendererCategory(categorized_value["value"], symbol, "test")
                    ranges.append(range)
            case "marker":
                    return None #Not implement
            case other:  
                    return None #Not implement
                
        render = QgsCategorizedSymbolRenderer(attribut, ranges)
        return render
    
    def _create_graduated_style(self,symbology: dict) -> QgsGraduatedSymbolRenderer:
        
        symbol = symbology["symbol"] 
        properties = symbology["properties"]
        attribut = properties["attributs"]
        ranges = []
        
        match symbol:
            case "fill":
                for graduated_value in properties["list_graduated"]:
                    properties = {
                        "outline_width" : graduated_value["outline_width"],
                        "outline_style" : graduated_value["outline_style"],
                        "outline_color" : graduated_value["outline_color"],
                    }
                    symbol = QgsFillSymbol.createSimple(properties)
                    symbol.setColor(QColor(graduated_value["color"]))

                    range = QgsRendererRange(graduated_value["min"], graduated_value["max"], symbol, "test")
                    ranges.append(range)
                
            case "line":
                for graduated_value in properties["list_graduated"]:
                    properties = {
                        "line_width" : graduated_value["outline_width"],
                        "line_style" : graduated_value["outline_style"],
                    }
                    symbol = QgsLineSymbol.createSimple(properties)
                    symbol.setColor(QColor(graduated_value["outline_color"]))

                    range = QgsRendererRange(graduated_value["min"], graduated_value["max"], symbol, "test")
                    ranges.append(range)
            case "marker": 
                for graduated_value in properties["list_graduated"]:
                    properties = {
                        # "outline_width" : graduated_value["outline_width"],
                        # "outline_style" : graduated_value["outline_style"],
                    }
                    symbol = QgsMarkerSymbol.createSimple(properties)
                    symbol.setColor(QColor(graduated_value["fill_color"]))
                    svg_layer = QgsSvgMarkerSymbolLayer("https://eop-storage-dev.s3.eu-west-3.amazonaws.com/asset/svg/apartment.svg")
                    svg_layer.setSize(10)
                    # svg_layer.setFillColor(QColor(graduated_value["fill_color"]))
                    # svg_layer.setStrokeColor(QColor(graduated_value["outline_color"]))
                    # svg_layer.setStrokeWidth(graduated_value["outline_width"])
                    symbol.changeSymbolLayer(0, svg_layer)
                    
                    range = QgsRendererRange(graduated_value["min"], graduated_value["max"], symbol, "test")
                    ranges.append(range)
            case other:  
                    return None #Not implement
                
        render = QgsGraduatedSymbolRenderer(attribut, ranges)
        render.setMode(QgsGraduatedSymbolRenderer.Custom) 
        return render

    def _create_single_symbol_style(self,symbology: dict) -> QgsSingleSymbolRenderer:
          
        symbol = symbology["symbol"]
        properties = symbology["properties"]
        
        match symbol: 
            case "line":
                render = QgsSingleSymbolRenderer(
                    QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
                )

                props = QgsSimpleLineSymbolLayer().properties()
                for key in properties.keys():
                    if key not in props:
                        return None

                symbol = QgsLineSymbol.createSimple(properties)
                symbol.layer
                render.setSymbol(symbol)
            case "fill":
                render = QgsSingleSymbolRenderer(
                    QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
                )

                props = QgsSimpleFillSymbolLayer().properties()
                for key in properties.keys():
                    if key not in props:
                        return None

                symbol = QgsFillSymbol.createSimple(properties)
                render.setSymbol(symbol)
            case "marker":
                render = QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(QgsWkbTypes.PointGeometry))
                properties["outline_width"] = 0.5
                properties["outline_style"] = "solid"
                properties["outline_color"] = "#FFFFFF"
                props = QgsSimpleMarkerSymbolLayer().properties()
                for key in properties.keys():
                    if key not in props:
                        return None

                symbol = QgsMarkerSymbol.createSimple(properties)
                
                effect_stack = QgsEffectStack()
                
                drop_shadow = QgsDropShadowEffect()

                drop_shadow.setColor(QColor(23, 23, 23, 127))  
                drop_shadow.setOffsetUnit(QgsUnitTypes.RenderPercentage)
                drop_shadow.setBlurUnit(QgsUnitTypes.RenderPercentage)
                drop_shadow.setBlurLevel(1.2)
                drop_shadow.setOffsetAngle(155)
                drop_shadow.setOffsetDistance(2.2)
                drop_shadow.setBlendMode(1)
                
                effect_stack.appendEffect(drop_shadow)

                source_effect = QgsDrawSourceEffect()
                source_effect.setEnabled(True)
                effect_stack.appendEffect(source_effect)

                for layer in symbol.symbolLayers():
                    layer.setPaintEffect(effect_stack)
                    
                    
                    
                render.setSymbol(symbol)
        return render


    def remove_style(self, name: str) -> bool:
        if name not in self.styles:
            return False, f"Style '{name}' does not exist"

        p = QgsProject()
        p.read(self._qgis_project_uri)

        for layer in p.mapLayers().values():
            if name == layer.styleManager().currentStyle():
                return False, f"Style is used by {layer.name()}"

        for layer in p.mapLayers().values():
            layer.styleManager().removeStyle(name)

        path = self._qgis_project_dir / f"{name}.qml"
        path.unlink()

        p.write()

        return True, ""

    def debug(self, msg: str) -> None:
        caller = f"{self.__class__.__name__}.{sys._getframe().f_back.f_code.co_name}"
        if StorageBackend.type() == StorageBackend.FILESYSTEM:
            msg = f"[{caller}][{self.name}] {msg}"
        else:
            msg = f"[{caller}][{self.schema}:{self.name}] {msg}"
        logger().debug(msg)

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

    @staticmethod
    def _layer_provider(layer_type: Qgis.LayerType, datasource: str) -> str:
        provider = ""
        if layer_type == Qgis.LayerType.Vector:
            provider = "ogr"
            if "table=" in datasource:
                provider = "postgres"
        elif layer_type == Qgis.LayerType.Raster:
            provider = "gdal"
        return provider

    @staticmethod
    def _layer_epsg_code(lyr) -> int:
        authid_items = lyr.crs().authid().split(":")
        if len(authid_items) < 2:
            return -1
        return int(authid_items[1])

    @staticmethod
    def _layer_bbox(lyr) -> list:
        return list(
            map(
                float,
                lyr.extent()
                .asWktCoordinates()
                .replace(",", "")
                .split(" "),
            )
        )

    @property
    def _qgis_project_uri(self) -> str:
        if StorageBackend.type() == StorageBackend.POSTGRESQL:
            service = config().qgisserver_projects_psql_service
            return f"postgresql:?service={service}&schema={self.schema}&project={self.name}"
        else:
            return (self._qgis_project_dir / f"{self.name}.qgs").as_posix()
