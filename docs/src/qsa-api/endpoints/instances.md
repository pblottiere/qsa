# QSA REST API : /api/instances

When `qsa-plugin` is installed, an `/api/instances` endpoint is available to
retrieve information about QGIS Server underlying instances.

| Method  |                      URL                      |         Description                        |
|---------|-----------------------------------------------|--------------------------------------------|
| GET     | `/api/instances`                              | List online QGIS Server instances          |
| GET     | `/api/instances/{instance}`                   | List QGIS Server instance metadata         |
| GET     | `/api/instances/{instance}/logs`              | Return logs of QGIS Server instance        |
| GET     | `/api/instances/{instance}/stats`             | Return stats of QGIS Server instance       |
