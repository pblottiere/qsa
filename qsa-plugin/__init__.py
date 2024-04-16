# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import struct
import pickle
import socket
from osgeo import gdal
from pathlib import Path
from threading import Thread
from datetime import datetime

from qgis import PyQt
from qgis.utils import server_active_plugins
from qgis.server import QgsConfigCache, QgsServerFilter
from qgis.core import Qgis, QgsProviderRegistry, QgsApplication

LOG_MESSAGES = []
CURRENT_TASK = {}
CURRENT_TASK_START = None


class ProbeFilter(QgsServerFilter):
    def __init__(self, iface):
        super().__init__(iface)

    def onRequestReady(self) -> bool:
        print("onRequestReady", file=sys.stderr)
        request = self.serverInterface().requestHandler()
        params = request.parameterMap()

        CURRENT_TASK["project"] = params.get("MAP", "")
        CURRENT_TASK["service"] = params.get("SERVICE", "")
        CURRENT_TASK["request"] = params.get("REQUEST", "")

        CURRENT_TASK_START = datetime.now()

        return True

    def onResponseComplete(self) -> bool:
        self._update()
        return True

    def onSendResponse(self) -> bool:
        self._update()
        return True

    def _update(self) -> None:
        CURRENT_TASK = {}
        CURRENT_TASK_START = None


def log_messages():
    m = {}
    m["logs"] = "\n".join(LOG_MESSAGES)
    return m


def stats():
    s = {}
    s["uptime"] = 0
    s["pid"] = 0
    s["cpu"] = 0
    s["memory"] = 0
    s["task"] = {}

    if CURRENT_TASK_START is not None and CURRENT_TASK:
        s["task"] = CURRENT_TASK
        s["task"]["duration"] = (datetime.now() - CURRENT_TASK_START).total_seconds() * 1000

    return s


def metadata(iface) -> dict:
    m = {}
    m["plugins"] = server_active_plugins

    m["versions"] = {}
    m["versions"]["qgis"] = f"{Qgis.version().split('-')[0]}"
    m["versions"]["qt"] = PyQt.QtCore.QT_VERSION_STR
    m["versions"]["python"] = sys.version.split(" ")[0]
    m["versions"]["gdal"] = gdal.__version__

    m["providers"] = QgsProviderRegistry.instance().pluginList().split("\n")

    m["cache"] = {}
    m["cache"]["projects"] = []
    for project in QgsConfigCache.instance().projects():
        m["cache"]["projects"].append(Path(project.fileName()).name)

    return m


def auto_connect(s: socket.socket, host: str, port: int) -> socket.socket:
    while True:
        print("Try to connect...", file=sys.stderr)
        try:
            s.connect((host, port))
            break
        except Exception as e:
            if e.errno == 106:
                s.close()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(5)
    print("Connected with QSA server", file=sys.stderr)
    return s


def f(iface, host: str, port: int) -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s = auto_connect(s, host, port)

    while True:
        try:
            data = s.recv(2000)

            payload = {}
            if b"metadata" in data:
                payload = metadata(iface)
            elif b"logs" in data:
                payload = log_messages()
            elif b"stats" in data:
                payload = stats()

            ser = pickle.dumps(payload)
            s.sendall(struct.pack(">I", len(ser)))
            s.sendall(ser)
        except Exception as e:
            print(e, file=sys.stderr)
            s = auto_connect(s, host, port)


def capture_log_message(message, tag, level):
    LOG_MESSAGES.append(message)


def serverClassFactory(iface):
    QgsApplication.instance().messageLog().messageReceived.connect(
        capture_log_message
    )

    host = str(os.environ.get("QSA_HOST", "localhost"))
    port = int(os.environ.get("QSA_PORT", 9999))

    t = Thread(
        target=f,
        args=(
            iface,
            host.replace('"', ""),
            port,
        ),
    )
    t.start()

    iface.registerFilter(ProbeFilter(iface), 100)
