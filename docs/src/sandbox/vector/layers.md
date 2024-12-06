# Sandbox : vector layers

Layers are based on the `data.gpkg` file mounted in the Docker containers.

## Add layers

To add a polygon layer from a geopackage to a project:

```` console
$ curl "http://localhost:5000/api/projects/my_project/layers?schema=my_schema" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "crs": 4326,
    "datasource":"/data.gpkg|layername=polygons",
    "name":"polygons",
    "type":"vector"
  }'
````

And a line layer from PostGIS:

```` console
# copy geopackage table to PostGIS
$ ogr2ogr -f PostgreSQL "PG:dbname=qsa password=qsa user=qsa port=5433 host=localhost" data.gpkg lines

# add a line layer based on the PostGIS table
$ curl "http://localhost:5000/api/projects/my_project/layers?schema=my_schema" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "crs": 4326,
    "datasource":"service=qsa table=\"public\".\"lines\" (geom)",
    "name":"lines",
    "type":"vector"
  }'
````

## List layers and get metadata

```` console
$ curl "http://localhost:5000/api/projects/my_project/layers?schema=my_schema"
["lines","polygons"]
````

```` console
$ curl "http://localhost:5000/api/projects/my_project/layers/lines?schema=my_schema" | jq
{
  "bbox": "-117.62319839219100004 23.20820580488510032, -82.32264950769270229 46.18290982947510059",
  "crs": "EPSG:4326",
  "current_style": "default",
  "geometry": "MultiLineString",
  "name": "lines",
  "source": "service='qsa' key='fid' checkPrimaryKeyUnicity='1' table=\"public\".\"lines\" (geom)",
  "styles": [
    "default"
  ],
  "type": "vector",
  "valid": true
}
````

## Map sample

To execute a WMS `GetMap` request with basic parameters:

```` console
$ curl "http://localhost:5000/api/projects/my_project/layers/polygons/map?schema=my_schema" --output map.png
````

<img src="../../images/map.png" width="300">

## Delete layers

```` console
$ curl -X DELETE "http://localhost:5000/api/projects/my_project/layers/lines?schema=my_schema"

$ curl "http://localhost:5000/api/projects/my_project/layers?schema=my_schema"
["polygons"]
````
