# coding: utf8

from pathlib import Path

from qgis.core import (
    QgsSymbol,
    QgsFeatureRenderer,
    QgsReadWriteContext,
)

from qgis.PyQt.QtXml import QDomDocument, QDomNode


RENDERER_TAG_NAME = "renderer-v2"  # constant from core/symbology/renderer.h


class VectorSymbologyRenderer:
    @staticmethod
    def style_is_vector(path: Path) -> bool:
        with open(path, "r") as file:
            if RENDERER_TAG_NAME in file.read():
                return True
        return False

    @staticmethod
    def style_to_json(path: Path) -> (dict, str):
        doc = QDomDocument()
        doc.setContent(open(path.as_posix()).read())
        node = QDomNode(doc.firstChild())

        renderer_node = node.firstChildElement(RENDERER_TAG_NAME)
        renderer = QgsFeatureRenderer.load(
            renderer_node, QgsReadWriteContext()
        )

        if renderer is None:
            return {}, f"Internal error: vector style {path} cannot be loaded"

        symbol = renderer.symbol()
        props = symbol.symbolLayer(0).properties()
        opacity = symbol.opacity()
        
        geom = "line"
        symbol = QgsSymbol.symbolTypeToString(symbol.type()).lower()
        if symbol == "fill":
            geom = "polygon"

        m = {}
        m["name"] = path.stem
        m["type"] = "vector"

        m["symbology"] = {}
        m["symbology"]["type"] = "single_symbol"
        m["symbology"]["properties"] = props
        m["symbology"]["symbol"] = symbol
        m["symbology"]["geometry"] = geom

        m["rendering"] = {}
        m["rendering"]["opacity"] = opacity
        print("là ",m)
        return m, ""
