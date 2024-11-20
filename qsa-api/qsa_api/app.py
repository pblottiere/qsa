# coding: utf8

import click
from flask import Flask

from qsa_api.config import QSAConfig
from qsa_api.monitor import QSAMonitor
from qsa_api.api.projects import projects
from qsa_api.api.symbology import symbology
from qsa_api.api.instances import instances
from qsa_api.api.processing import processing

app = Flask(__name__)


class QSA:
    def __init__(self) -> None:
        print("Run DEBUG MODE : filter_branch 1")
        self.cfg = QSAConfig()
        if not self.cfg.is_valid:
            return

        self.monitor = None
        if self.cfg.monitoring_port:
            self.monitor = QSAMonitor(self.cfg)
            self.monitor.start()

        app.config["CONFIG"] = self.cfg
        app.config["MONITOR"] = self.monitor
        app.register_blueprint(projects, url_prefix="/api/projects")
        app.register_blueprint(symbology, url_prefix="/api/symbology")
        app.register_blueprint(instances, url_prefix="/api/instances")
        app.register_blueprint(processing, url_prefix="/api/processing")

        app.logger.setLevel(self.cfg.loglevel)

    def run(self):
        app.run(host="0.0.0.0", threaded=False)


qsa = QSA()


@click.command()
def run():
    qsa.run()
