# Sandbox

The sandbox directory provides a plug-and-play `Docker` environment to discover
QSA tools with PostgreSQL support enabled.

First, a QSA REST API server is set up with 4 QGIS Server instances:

```` console
$ cd sandbox
$ docker-compose up --scale qgisserver=4 -d
$ docker ps
CONTAINER ID   IMAGE                              COMMAND                  CREATED       STATUS         PORTS                                       NAMES
d2eaf6bdfae4   pblottiere/qsa          "gunicorn -b 0.0.0.0…"   2 hours ago   Up 10 seconds  0.0.0.0:5000->5000/tcp, :::5000->5000/tcp   sandbox-qsa-1
b47085d9ad65   postgis/postgis:15      "docker-entrypoint.s…"   5 days ago    Up 9 seconds   0.0.0.0:5433->5432/tcp, :::5433->5432/tcp   sandbox-postgres-1
77fa87641b42   qgis/qgis-server:3.38   "/bin/sh -c /usr/loc…"   2 hours ago   Up 9 seconds   80/tcp, 9993/tcp                            sandbox-qgisserver-1
093346c82ea8   qgis/qgis-server:3.38   "/bin/sh -c /usr/loc…"   2 hours ago   Up 9 seconds   80/tcp, 9993/tcp                            sandbox-qgisserver-2
afd95ccaef9e   qgis/qgis-server:3.38   "/bin/sh -c /usr/loc…"   2 hours ago   Up 9 seconds   80/tcp, 9993/tcp                            sandbox-qgisserver-3
0b13f3d867c5   qgis/qgis-server:3.38   "/bin/sh -c /usr/loc…"   2 hours ago   Up 8 seconds   80/tcp, 9993/tcp                            sandbox-qgisserver-4
````
