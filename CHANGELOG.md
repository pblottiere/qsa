# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [1.1.0] - 2024-09-24

### Added

- Add Python files after installation of dependencies in Dockerfile : <https://github.com/pblottiere/QSA/pull/68>
- Add basic cache entrypoints : <https://github.com/pblottiere/QSA/pull/74>
- Add data type and band counts metadata for raster layers : <https://github.com/pblottiere/QSA/pull/80>

### Fixed

- Always create parent directory for internal sqlite database : <https://github.com/pblottiere/QSA/pull/73>
- Clear MapProxy legends cache : <https://github.com/pblottiere/QSA/pull/78>

## [1.0.0] - 2024-07-31

### Added

- Add qsa-plugin, qsa-cli and doc: <https://github.com/pblottiere/QSA/pull/8>
- Add raster layer support: <https://github.com/pblottiere/QSA/pull/9>
- Add a CHANGELOG file: <https://github.com/pblottiere/QSA/pull/10>
- Add basic badges in README: <https://github.com/pblottiere/QSA/pull/11>
- Add qsa-cli stats command: <https://github.com/pblottiere/QSA/pull/13>
- Add PostgreSQL support for storing QGIS projects: <https://github.com/pblottiere/QSA/pull/15>
- Add doc for raster layer in sandbox: <https://github.com/pblottiere/QSA/pull/16>
- Add basic support for raster style: <https://github.com/pblottiere/QSA/pull/17>
- Add support for min/max settings in raster style: <https://github.com/pblottiere/QSA/pull/18>
- CRS is now optional when adding a layer: <https://github.com/pblottiere/QSA/pull/19>
- Manage optional CRS when MapProxy is enabled: <https://github.com/pblottiere/QSA/pull/20>
- Optimize raster cache config: <https://github.com/pblottiere/QSA/pull/21>
- Add PostGIS support for vector layers: <https://github.com/pblottiere/QSA/pull/22>
- Add option to build overview if necessary: <https://github.com/pblottiere/QSA/pull/24>
- Add QSA_LOGLEVEL environment variable: <https://github.com/pblottiere/QSA/pull/27>
- Add check on epsg code validity: <https://github.com/pblottiere/QSA/pull/29>
- Optimize MapProxy clear cache: <https://github.com/pblottiere/QSA/pull/31>
- Homogenize gray band properties with red/green/blue: <https://github.com/pblottiere/QSA/pull/32>
- Optimize min/max statistics computation: <https://github.com/pblottiere/QSA/pull/34>
- Update QSA app to be used with a proper WSGI HTTP production server: <https://github.com/pblottiere/QSA/pull/38>
- Add singleband pseudocolor renderer: <https://github.com/pblottiere/QSA/pull/39>
- Use QGIS 3.38 in sandbox: <https://github.com/pblottiere/QSA/pull/41>
- Add support for WMS TIME parameter: <https://github.com/pblottiere/QSA/pull/42>
- Add gradient stops for singlebandpseudocolor renderer: <https://github.com/pblottiere/QSA/pull/43>
- Adapt docs how to run tests: <https://github.com/pblottiere/QSA/pull/49>
- Add /api/processing/raster/calculator entrypoint: <https://github.com/pblottiere/QSA/pull/45>
- Add /api/processing/raster/histogram: <https://github.com/pblottiere/QSA/pull/52>
- Activate legend in MapProxy configuration: <https://github.com/pblottiere/QSA/pull/53>
- CI: add unit test without Postgres dependency: <https://github.com/pblottiere/QSA/pull/50>
- Add MapProxy s3 cache support: <https://github.com/pblottiere/QSA/pull/55>
- Move histogram computation in dedicated process: <https://github.com/pblottiere/QSA/pull/56>
- Build 'dev' container image on push to 'main' branch: <https://github.com/pblottiere/QSA/pull/61>
- Optimize project opening: <https://github.com/pblottiere/QSA/pull/58>
- Add global try/except for requests: <https://github.com/pblottiere/QSA/pull/62>
- Add badge for CI: <https://github.com/pblottiere/QSA/pull/63>

### Fixed

- Fix projects in cache in qsa-plugin: <https://github.com/pblottiere/QSA/pull/12>
- Fix docs: <https://github.com/pblottiere/QSA/pull/14>
- Deactivate multithreading: <https://github.com/pblottiere/QSA/pull/23>
- Fix get style for raster (and homogenize vector style): <https://github.com/pblottiere/QSA/pull/25>
- Remove log in staticmethod: <https://github.com/pblottiere/QSA/pull/30>
- Remove useless print in tests: <https://github.com/pblottiere/QSA/pull/54>

## [0.0.2] - 2024-02-15

### Added

- Support simple symbol properties for lines and polygons: <https://github.com/pblottiere/QSA/pull/1>
- Add support for simple marker style: <https://github.com/pblottiere/QSA/pull/2>

## [0.0.1] - 2024-02-12

### Added

- API to create QGIS projects with vector layer and MapProxy cache
