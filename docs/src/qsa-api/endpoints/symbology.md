# QSA REST API : /api/symbology

Vector layers rendering can be configured with several kinds of symbols
according to the geometry type. The [symbol selector](https://docs.qgis.org/3.34/en/docs/user_manual/style_library/symbol_selector.html)
in QGIS is very dense but for now, only `Marker`, `Line` and `Fill` simple
symbols are supported.

The `/api/symbology` endpoint allows to dynamically retrieve the corresponding
parameters as well as raster renderer properties depending on QGIS Server
version.

| Method  |                      URL                                                  |         Description                          |
|---------|---------------------------------------------------------------------------|----------------------------------------------|
| GET     | `/api/symbology/vector/point/single_symbol/marker/properties`             | Marker simple symbol properties              |
| GET     | `/api/symbology/vector/line/single_symbol/line/properties`                | Line simple symbol properties                |
| GET     | `/api/symbology/vector/polygon/single_symbol/fill/properties`             | Polygon simple symbol properties             |
| GET     | `/api/symbology/vector/rendering/properties`                              | Vector layer rendering properties            |
| GET     | `/api/symbology/raster/singlebandgray/properties`                         | Single band gray properties                  |
| GET     | `/api/symbology/raster/multibandcolor/properties`                         | Multi band color properties                  |
| GET     | `/api/symbology/raster/singlebandpseudocolor/properties`                  | Single band pseudocolor properties           |
| GET     | `/api/symbology/raster/singlebandpseudocolor/ramp/{name}/properties`      | Single band pseudocolor ramp properties      |
| GET     | `/api/symbology/raster/rendering/properties`                              | Raster layer rendering properties            |

Examples:

```` console
# Return single symbol properties for polygon layers
$ curl "http://localhost:5000/api/symbology/vector/polygon/single_symbol/fill/properties" | jq
{
  "border_width_map_unit_scale": "3x:0,0,0,0,0,0",
  "color": "0,0,255,255",
  "joinstyle": "bevel",
  "offset": "0,0",
  "offset_map_unit_scale": "3x:0,0,0,0,0,0",
  "offset_unit": "MM",
  "outline_color": "35,35,35,255",
  "outline_style": "solid (no, solid, dash, dot, dash dot, dash dot dot)",
  "outline_width": "0.26",
  "outline_width_unit": "MM",
  "style": "solid"
}

# Return multi band gray properties for raster layers
$ curl "http://localhost:5000/api/symbology/raster/multibandcolor/properties" | jq
{
  "blue": {
    "band": 3,
    "min": 0.0,
    "max": 1.0
  },
  "green": {
    "band": 2,
    "min": 0.0,
    "max": 1.0
  },
  "red": {
    "band": 1,
    "min": 0.0,
    "max": 1.0
  }
  "contrast_enhancement": {
    "algorithm": "StretchToMinimumMaximum (StretchToMinimumMaximum, NoEnhancement)",
    "limits_min_max": "MinMax (MinMax, UserDefined)"
  }
}
````
