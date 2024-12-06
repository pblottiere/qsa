# QSA REST API : installation

## From sources

```` console
$ cd qsa-api
$ virtualenv --system-site-packages venv  # system aware for pyqgis
$ . venv/bin/activate
(venv)$ pip install poetry
(venv)$ poetry install
````

## Docker image

A prebuilt image can be found on `ghcr.io/pblottiere/qsa`:

```` console
$ docker pull ghcr.io/pblottiere/qsa:1.1.0
````

Otherwise the image can manually be built using:
`docker build -t my-custom-qsa-image .`. See [Sandbox](../sandbox/index.html)
for details how to use it.
