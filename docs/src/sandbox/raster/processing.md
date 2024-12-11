# Sandbox : raster processing

## Histogram

To get an histogram for a specific raster layer:

```` console
$ curl "http://localhost:5000/api/processing/raster/histogram/my_project/dem?schema=my_schema" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "min": 0,
    "count": 100
  }'
````
