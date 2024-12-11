# QSA REST API : /api/projects

## Project

A QSA project is defined by:

* a QGIS project
* a list of themes
* an internal SQLite database
* a MapProxy configuration file (if enabled)

| Method  |                      URL                      |         Description                                                                                 |
|---------|-----------------------------------------------|-----------------------------------------------------------------------------------------------------|
| GET     | `/api/projects`                               | List projects                                                                                       |
| GET     | `/api/projects/{project}`                     | List project's metadata                                                                             |
| POST    | `/api/projects/`                              | Create a project with `name`, `author` and `schema` (only used when PostgreSQL support is enabled)  |
| DELETE  | `/api/projects/{project}`                     | Remove a project                                                                                    |

Examples:

``` console
# create a project and store the QGIS project in PostgreSQL within `my_schema`
$ curl "http://localhost/api/projects/" \
     -X POST \
     -H 'Content-Type: application/json' \
     -d '{
        "name":"my_project",
        "author":"pblottiere",
        "schema":"my_schema"
     }'

# get metadata about the project stored in PostgreSQL
$ curl "http://localhost/api/projects/my_project?schema=my_schema"
```

## Layer

When a layer is added/removed to a QSA project, the corresponding QGIS project
is updated. When MapProxy cache management is enabled, the configuration file is
updated as well and the cache may be cleaned if necessary (for example when the
current style is updated).

Several themes can be associated with a layer like in QGIS Desktop, but only
the current one is used when the `STYLE` parameter in OGC web services is
empty.

| Method  |                      URL                         |         Description                                                                                                                                |
|---------|--------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| GET     | `/api/projects/{project}/layers`                 | List layers in project                                                                                                                             |
| GET     | `/api/projects/{project}/layers/{layer}`         | List layer's metadata                                                                                                                              |
| GET     | `/api/projects/{project}/layers/{layer}/map`     | WMS `GetMap` result with default parameters                                                                                                        |
| GET     | `/api/projects/{project}/layers/{layer}/map/url` | WMS `GetMap` URL with default parameters                                                                                                           |
| POST    | `/api/projects/{project}/layers`                 | Add layer to project. See [Layer definition](#layer-definition) for more information.                                                              |
| POST    | `/api/projects/{project}/layers/{layer}/style`   | Add/Update layer's style with `name` (style name) and `current` (`true` or `false`)                                                                |
| DELETE  | `/api/projects/{project}/layers/{layer}`         | Remove layer from project                                                                                                                          |

### Layer definition {#layer-definition}

A layer can be added to a project thanks to the next parameters:

* `type` : `raster` or `vector`
* `name` : the layer's name
* `datasource` : the link to the datasource according to the storage backend
  * filesystem : `/tmp/raster.tif`
  * AWS S3 : `/vsis3/bucket/raster.tif`
  * PostGIS : `service=qsa table=\"public\".\"lines\" (geom)`
* `overview` (optional) : automatically build overviews for raster layers stored in S3 buckets
* `crs` (optional) : CRS (automatically detected by default)

Example:

```` console
# Add a FlatGeobuf vector layer stored on S3 bucket in project `my_project`
$ curl "http://localhost/api/projects/my_project/layers" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "name":"my_layer",
    "type":"vector",
    "datasource":"/vsis3/my-storage/vector/my_layer.fgb"
  }'
````

## Style

A QSA style may be used through the `STYLE` OGC web services parameter to
specify the rendering for a specific layer. Default styles may be defined and
automatically used when a vector layer is added to a QSA project.

| Method  |                      URL                      |         Description                                                                                                            |
|---------|-----------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| GET     | `/api/projects/{project}/styles`              | List styles in project                                                                                                         |
| GET     | `/api/projects/{project}/styles/default`      | List default styles in project                                                                                                 |
| GET     | `/api/projects/{project}/styles/{style}`      | List style's metadata                                                                                                          |
| POST    | `/api/projects/{project}/styles/{style}`      | Add style to project. See [Vector style](#vector-style) and [Raster style](#raster-style) for more information.                |
| POST    | `/api/projects/{project}/styles/default`      | Set a default layer's style. See [Vector style](#vector-style) and [Raster style](#raster-style) for more information.         |
| DELETE  | `/api/projects/{project}/styles/{style}`      | Remove style from project                                                                                                      |

### Vector style {#vector-style}

For vector layers, a style can be defined with the parameters listed below:

* `type` : `vector`
* `name` : the name of the style
* `rendering` : rendering parameters (only `opacity` is supported for now)
* `symbology` : dictionary with `type` (only `single_symbol` is supported for
                now), `symbol` and `properties`

Example:

```` console
# Add a style for point geometry vector layers
$ curl "http://localhost:5000/api/projects/my_project/styles" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "vector",
    "name": "my_marker_style",
    "rendering": {
      "opacity": 100.
    },
    "symbology": {
      "type": "single_symbol",
      "symbol": "marker",
      "properties": {
        "color": "#112233"
      }
    }
  }'
````

To set a default style for a specific geometry, the parameters listed below are available:

* `name` : the name of the style to use by default
* `geometry` : the geometry for which the style needs to be applied

#### Raster style {#raster-style}

For raster layers, a style can be defined with the parameters listed below:

* `type` : `raster`
* `name` : the name of the style
* `rendering` : rendering parameters
* `symbology` : dictionary with `type` (only `singlebandgray` and
  `multibandcolor` are supported for now) and `properties`

Example:

```` console
# Add a style for multiband raster
$ curl "http://localhost:5000/api/projects/my_project/styles" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "raster",
    "name": "my_multiband_style",
    "rendering": {
      "saturation": 3,
      "brightness": -148,
      "contrast": 42,
      "gamma": 4.
    },
    "symbology": {
      "type": "multibandcolor",
      "properties": {
        "red": {
          "band": 1
        },
        "green": {
          "band": 2
        },
        "blue": {
          "band": 3
        }
      }
    }
  }'
````

## Cache

| Method  |                      URL                         |         Description                                                                                                          |
|---------|--------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| GET     | `/api/projects/{project}/cache`                  | Return metadata about the cache                                                                                              |
| POST    | `/api/projects/{project}/cache/reset`            | Clear cached data and reset cache configuration                                                                              |

Example:

```` console
$ curl "http://localhost:5000/api/projects/my_project/cache"
{
  "valid":true,
  "storage":"filesystem"
}
````

<div class="warning">
Reset cache

When a QGIS project is created manually without QSA, the cache is not
initialized. This method allows to create the MapProxy configuration file
accordingly.
</div>
