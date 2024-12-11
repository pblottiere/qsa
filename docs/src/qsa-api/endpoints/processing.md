# QSA REST API : /api/processing

The QSA REST API provides some basic processing methods to create on-the-fly
rasters or get histogram for raster layers.

| Method  |                      URL                              |         Description                                                  |
|---------|-------------------------------------------------------|----------------------------------------------------------------------|
| POST    | `/api/processing/raster/histogram/{project}/{layer}`  | Return an histogram in JSON                                          |
| POST    | `/api/processing/raster/calculator/{project}`         | Create a raster based on an `expression` and an `output` filename    |

Examples:

``` console
# create a new layer based on a QGIS expression
$ curl "http://localhost/api/projects/" \
     -X POST \
     -H 'Content-Type: application/json' \
     -d '{
        "expression":"layer@1 + 10",
        "output":"/vsis3/my-storage/result.tif"
     }'
```

<div class="warning">
Processing

These are basic processing methods but one could argue that WPS or OGC API
Processes should be used instead.
</div>
