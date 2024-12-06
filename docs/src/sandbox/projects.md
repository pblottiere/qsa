# Sandbox : projects

## Create and delete projects in PostgreSQL

First we create a schema to store QGIS projects:

```` console
$ psql -h localhost -p 5433 -U qsa qsa -c "create schema my_schema"
CREATE SCHEMA
````

Then we create a QSA project:

```` console
$ curl "http://localhost:5000/api/projects/" \
    -X POST \
    -H 'Content-Type: application/json' \
    -d '{
        "name":"my_project",
        "author":"pblottiere",
        "schema":"my_schema"
    }'
````

In this case, a directory has been created on the filesystem with the internal
QSA database:

```` console
$ file projects/qsa/my_schema_my_project/qsa.db
SQLite 3.x database
````

And a QGIS project has been created in PostgreSQL:

```` console
$ psql -h localhost -p 5433 -U qsa qsa -c "select name from my_schema.qgis_projects"
    name
------------
 my_project
(1 row)
````

To create another project in `public` schema and list available projects thanks
to the QSA API:

```` console
$ curl "http://localhost:5000/api/projects/" \
    -X POST \
    -H 'Content-Type: application/json' \
    -d '{
        "name":"my_project_2",
        "author":"pblottiere"
    }'
true
$ curl "http://localhost:5000/api/projects/"
["my_project_2"]
$ curl "http://localhost:5000/api/projects/?schema=my_schema"
["my_project"]
````

To delete a project:

```` console
$ curl -X DELETE "http://localhost:5000/api/projects/my_project_2"
true
$ curl "http://localhost:5000/api/projects/"
[]
````

To list project metadata:

```` console
$ curl http://localhost:5000/api/projects/my_project?schema=my_schema | jq
{
  "author": "pblottiere",
  "creation_datetime": "2024-03-14T20:17:45",
  "crs": "EPSG:3857",
  "schema": "my_schema",
  "storage": "postgresql"
}
````
