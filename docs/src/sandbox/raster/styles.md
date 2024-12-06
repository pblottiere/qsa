# Sandbox : raster styles

## Add style to project

To add a style for a multiband raster layer:

```` console
$ curl "http://localhost:5000/api/projects/my_project/styles?schema=my_schema" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "raster",
    "name": "my_singlebandgray_style",
    "symbology": {
      "type": "singlebandgray",
      "properties": {
        "gray": {
          "band": 1
        },
        "contrast_enhancement": {
          "algorithm": "StretchToMinimumMaximum",
          "limits_min_max": "MinMax"
        }
      }
    },
    "rendering": {
      "brightness": 255,
      "gamma": 0.1,
      "contrast": 100
    }
  }'
````

To list styles for a specific project:

```` console
$ curl "http://localhost:5000/api/projects/my_project/styles?schema=my_schema"
["my_singlebandgray_style"]
````

## Apply style to layer

To apply a specific style to a layer:

```` console
$ curl "http://localhost:5000/api/projects/my_project/layers/dem/style?schema=my_schema" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "name":"my_singlebandgray_style",
    "current":true
  }'
````

The layer rendering has changed now:

```` console
$ curl "http://localhost:5000/api/projects/my_project/layers/dem/map?schema=my_schema" --output map.png
````

<img src="../../images/map_raster_style.png" width="300">
