# Sandbox : raster layers

Layer is based on the `landsat_4326.tif` file mounted in the Docker containers.

## Add layers

To add a raster layer to a project:

```` console
$ curl "http://localhost:5000/api/projects/my_project/layers?schema=my_schema" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "datasource":"/dem.tif",
    "name":"dem",
    "type":"raster"
  }'
````

## List layers and get metadata

```` console
# list layers
$ curl "http://localhost:5000/api/projects/my_project/layers?schema=my_schema"
["polygons","dem"]

# get metadata
$ curl "http://localhost:5000/api/projects/my_project/layers/dem?schema=my_schema"
{
  "bands": 1,
  "bbox": "18.6662979442000001 45.77670143760000343, 18.70359794419999844 45.81170143760000002",
  "crs": "EPSG:4326",
  "current_style": "default",
  "data_type": "float32",
  "name": "dem",
  "source": "/dem.tif",
  "styles": [
    "default"
  ],
  "type": "raster",
  "valid": true
}
````

## Map sample

To execute a WMS `GetMap` request with basic parameters:

```` console
$ curl "http://localhost:5000/api/projects/my_project/layers/dem/map?schema=my_schema" --output map.png
````

<img src="../../images/raster_dem_map.png" width="300">
