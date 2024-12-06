# Sandbox : introspection

`qsa-cli` allows to inspect online QGIS Server instances registered to
`qsa-api` server, but it's also possible to use the REST API.

## List online instances

To list these instances with `qsa-cli`:

```` console
$ QSA_SERVER_URL=http://localhost:5000 qsa ps
INSTANCE ID    IP          STATUS
-------------  ----------  -----------------------
6773ca08       172.20.0.2  Binded 1096 seconds ago
4464d3c5       172.20.0.4  Binded 1096 seconds ago
012083b9       172.20.0.5  Binded 1096 seconds ago
c0047e66       172.20.0.6  Binded 1096 seconds ago
````

Or with the API:

```` console
$ curl http://localhost:5000/api/instances/ | jq
{
  "servers": [
    {
      "binded": 1217,
      "id": "6773ca08",
      "ip": "172.20.0.2"
    },
    {
      "binded": 1217,
      "id": "4464d3c5",
      "ip": "172.20.0.4"
    },
    {
      "binded": 1217,
      "id": "012083b9",
      "ip": "172.20.0.5"
    },
    {
      "binded": 1217,
      "id": "c0047e66",
      "ip": "172.20.0.6"
    }
  ]
}
````

## Get metadata

To get some metadata about a specific QGIS Server instance with `qsa-cli`:

```` console
$ qsa inspect 4464d3c5
{
  "cache": {
    "projects": []
  },
  "plugins": [
    "qsa"
  ],
  "providers": [
    "OGC API - Features data provider",
    "WFS data provider",
    "ArcGIS Feature Service data provider",
    "ArcGIS Map Service data provider",
    "COPC point cloud data provider",
    "Delimited text data provider",
    "EPT point cloud data provider",
    "GDAL data provider",
    "GPS eXchange format provider",
    "SAP HANA spatial data provider",
    "MDAL provider",
    "Memory provider",
    "Mesh memory provider",
    "MSSQL spatial data provider",
    "OGR data provider",
    "PDAL point cloud data provider",
    "PostgreSQL/PostGIS data provider",
    "Postgres raster provider",
    "SpatiaLite data provider",
    "Vector tile provider",
    "Virtual layer data provider",
    "Virtual Raster data provider",
    "OGC Web Coverage Service version 1.0/1.1 data provider",
    "OGC Web Map Service version 1.3 data provider",
    ""
  ],
  "versions": {
    "gdal": "3.4.1",
    "python": "3.10.6",
    "qgis": "3.30.3",
    "qt": "5.15.3"
  }
}
````

Or with the API `curl http://localhost:5000/api/instances/4464d3c5`.

## Fetch the log

A bad request to QGIS Server to have something in the log:

```` console
$ curl http://172.20.0.4/ogc/
<?xml version="1.0" encoding="UTF-8"?>
<ServerException>Project file error. For OWS services: please provide a SERVICE and a MAP parameter pointing to a valid QGIS project file</ServerException>
````

Then to fetch the log of the corresponding QGIS Server instance with `qsa-cli`:

```` console
$ qsa logs 4464d3c5
Server plugin qsa loaded!
Server python plugins loaded
******************** New request ***************
Request URL: http://172.20.0.4/ogc/?map=/io/data//.qgs
Environment:
------------------------------------------------
SERVER_NAME: 172.20.0.4
REQUEST_URI: /ogc/
SCRIPT_NAME: /qgis/qgis_mapserv.fcgi
HTTPS:
REMOTE_ADDR: 172.20.0.1
SERVER_PORT: 80
QUERY_STRING: map=/io/data//.qgs
REMOTE_USER:
CONTENT_TYPE:
REQUEST_METHOD: GET
SERVER_PROTOCOL: HTTP/1.1
MAP:/io/data//.qgs
Error when loading project file '/io/data//.qgs': Unable to open /io/data//.qgs
Trying URL path: '/ogc/' for '/'
Trying URL path: '/ogc/' for '/wfs3'
<?xml version="1.0" encoding="UTF-8"?>
<ServerException>Project file error. For OWS services: please provide a SERVICE and a MAP parameter pointing to a valid QGIS project file</ServerException>

Request finished in 3 ms
````

## Display stats

To display stats for all QGIS Server online instances:

```` console
$ qsa stats
INSTANCE ID      COUNT  TIME        SERVICE    REQUEST    PROJECT
-------------  -------  ----------  ---------  ---------  ---------
4464d3c5             1
6773ca08             0
012083b9             0
c0047e66             0
````
