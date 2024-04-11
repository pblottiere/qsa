# coding: utf8

import shutil
import requests
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from flask import send_file, Blueprint, jsonify, request

from ..wms import WMS
from ..project import QSAProject


projects = Blueprint("projects", __name__)


@projects.get("/")
def projects_list():
    p = []
    for project in QSAProject.projects():
        p.append(project.name)
    return jsonify(p)


@projects.get("/<name>")
def project_info(name: str):
    project = QSAProject(name)

    if project.exists():
        return jsonify(QSAProject(name).metadata)
    return {"error": "Project does not exist"}, 415


@projects.post("/")
def project_add():
    schema = {
        "type": "object",
        "required": ["name", "author"],
        "properties": {
            "name": {"type": "string"},
            "author": {"type": "string"},
        },
    }

    if request.is_json:
        data = request.get_json()
        try:
            validate(data, schema)
        except ValidationError as e:
            return {"error": e.message}, 415

        name = data["name"]
        author = data["author"]

        project = QSAProject(name)
        if project.exists():
            return {"error": "Project already exists"}
        project.create(author)
        return jsonify(True), 201
    return {"error": "Request must be JSON"}, 415


@projects.delete("/<name>")
def project_del(name):
    project = QSAProject(name)
    if project.exists():
        project.remove()
        return jsonify(True), 201
    return {"error": "Project does not exist"}, 415


@projects.get("/<name>/styles")
def project_styles(name):
    project = QSAProject(name)
    if project.exists():
        return jsonify(project.styles), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.get("/<name>/styles/<style>")
def project_style(name, style):
    project = QSAProject(name)
    if project.exists():
        infos = project.style(style)
        return jsonify(infos), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.delete("/<name>/styles/<style>")
def project_del_style(name, style):
    project = QSAProject(name)
    if project.exists():
        if style in project.styles:
            rc = project.remove_style(style)
            return jsonify(rc), 201
        else:
            return {"error": "Style does not exist"}, 415
    else:
        return {"error": "Project does not exist"}, 415


@projects.post("/<name>/layers/<layer_name>/style")
def project_layer_update_style(name, layer_name):
    schema = {
        "type": "object",
        "required": ["name", "current"],
        "properties": {
            "name": {"type": "string"},
            "current": {"type": "boolean"},
        },
    }

    project = QSAProject(name)
    if project.exists():
        data = request.get_json()
        try:
            validate(data, schema)
        except ValidationError as e:
            return {"error": e.message}, 415

        current = data["current"]
        style_name = data["name"]
        rc, msg = project.layer_update_style(layer_name, style_name, current)
        if not rc:
            return {"error": msg}, 415
        return jsonify(True), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.get("/<name>/layers/<layer_name>/map/url")
def project_layer_map_url(name, layer_name):
    project = QSAProject(name)
    if project.exists():
        getmap = WMS.getmap_url(name, layer_name)
        return jsonify({"url": getmap}), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.get("/<name>/layers/<layer_name>/map")
def project_layer_map(name, layer_name):
    project = QSAProject(name)
    if project.exists():
        url = WMS.getmap(name, layer_name)
        r = requests.get(url, stream=True)

        png = "/tmp/map.png"
        with open(png, "wb") as out_file:
            shutil.copyfileobj(r.raw, out_file)

        return send_file(png, mimetype="image/png")
    else:
        return {"error": "Project does not exist"}, 415


@projects.post("/<name>/styles")
def project_add_style(name):
    schema = {
        "type": "object",
        "required": ["name", "symbol", "symbology", "properties"],
        "properties": {
            "name": {"type": "string"},
            "symbol": {"type": "string"},
            "symbology": {"type": "string"},
            "properties": {"type": "object"},
        },
    }

    project = QSAProject(name)
    if project.exists():
        data = request.get_json()
        try:
            validate(data, schema)
        except ValidationError as e:
            return {"error": e.message}, 415

        # legacy support
        symbology = data["symbology"]
        if symbology == "single symbol":
            symbology = "single_symbol"

        rc = project.add_style(
            data["name"],
            data["symbol"],
            data["symbology"],
            data["properties"],
        )
        return jsonify(rc), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.get("/<name>/styles/default")
def project_default_styles(name):
    project = QSAProject(name)
    if project.exists():
        infos = project.default_styles()
        return jsonify(infos), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.post("/<name>/styles/default")
def project_update_default_style(name):
    schema = {
        "type": "object",
        "required": ["geometry", "style"],
        "properties": {
            "geometry": {"type": "string"},
            "style": {"type": "string"},
        },
    }

    project = QSAProject(name)
    if project.exists():
        data = request.get_json()
        try:
            validate(data, schema)
        except ValidationError as e:
            return {"error": e.message}, 415

        project.style_update(data["geometry"], data["style"])
        return jsonify(True), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.get("/<name>/layers")
def project_layers(name):
    project = QSAProject(name)
    if project.exists():
        return jsonify(project.layers), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.post("/<name>/layers")
def project_add_layer(name):
    schema = {
        "type": "object",
        "required": ["name", "datasource", "crs", "type"],
        "properties": {
            "name": {"type": "string"},
            "datasource": {"type": "string"},
            "crs": {"type": "number"},
            "type": {"type": "string"},
        },
    }

    project = QSAProject(name)
    if project.exists():
        data = request.get_json()
        try:
            validate(data, schema)
        except ValidationError as e:
            return {"error": e.message}, 415

        rc, err = project.add_layer(
            data["datasource"], data["type"], data["name"], data["crs"]
        )
        if rc:
            return jsonify(rc), 201
        else:
            return {"error": err}, 415
    else:
        return {"error": "Project does not exist"}, 415


@projects.get("/<name>/layers/<layer_name>")
def project_info_layer(name, layer_name):
    project = QSAProject(name)
    if project.exists():
        layer_infos = project.layer(layer_name)
        if layer_infos:
            return jsonify(layer_infos), 201
        else:
            return {"error": "Layer does not exist"}, 415
    else:
        return {"error": "Project does not exist"}, 415


@projects.delete("/<name>/layers/<layer_name>")
def project_del_layer(name, layer_name):
    project = QSAProject(name)
    if project.exists():
        if project.layer_exists(layer_name):
            rc = project.remove_layer(layer_name)
            return jsonify(rc), 201
        else:
            return {"error": "Layer does not exist"}, 415
    else:
        return {"error": "Project does not exist"}, 415
