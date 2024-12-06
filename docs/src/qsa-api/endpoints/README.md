# QSA REST API : endpoints

The QSA REST API provides several endpoints:

* [/api/symbology](symbology.md)
* [/api/projects](projects.md)
* [/api/instances](instances.md)
* [/api/processing](processing.md)

## PostgreSQL schema

When PostgreSQL support is enabled, a query string parameter `schema` may be
used to specify the schema in which the QGIS project is stored in the database
(`public` is used by default).

```` console
# call a specific endpoint using projects stored in PostgreSQL schema named `myschema`
$ curl "http://localhost/api/xxx/yyy?schema=myschema"
````
