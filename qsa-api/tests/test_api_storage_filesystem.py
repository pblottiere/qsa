import os
import unittest
from pathlib import Path

from .utils import TestClient

GPKG = Path(__file__).parent / "data.gpkg"
if "QSA_GPKG" in os.environ:
    GPKG = os.environ["QSA_GPKG"]

GEOTIFF = Path(__file__).parent / "landsat_4326.tif"
if "QSA_GEOTIFF" in os.environ:
    GEOTIFF = os.environ["QSA_GEOTIFF"]

TEST_PROJECT_0 = "qsa_test_project0"
TEST_PROJECT_1 = "qsa_test_project1"


class APITestCaseFilesystem(unittest.TestCase):
    def setUp(self):
        self.app = TestClient("/tmp/qsa/projects/qgis")

    def test_projects(self):
        # no projects
        p = self.app.get("/api/projects/")
        self.assertTrue(TEST_PROJECT_0 not in p.get_json())
        self.assertTrue(TEST_PROJECT_1 not in p.get_json())

        # add projects
        data = {}
        data["name"] = TEST_PROJECT_0
        data["author"] = "pblottiere"
        p = self.app.post("/api/projects/", data)
        self.assertEqual(p.status_code, 201)

        data = {}
        data["name"] = "qsa_test_project1"
        data["author"] = "pblottiere"
        p = self.app.post("/api/projects/", data)
        self.assertEqual(p.status_code, 201)

        # 2 projects
        p = self.app.get("/api/projects/")
        self.assertTrue(TEST_PROJECT_0 in p.get_json())
        self.assertTrue(TEST_PROJECT_1 in p.get_json())

        # remove project
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}")
        self.assertEqual(p.status_code, 201)

        # 1 projects
        p = self.app.get("/api/projects/")
        self.assertTrue(TEST_PROJECT_1 in p.get_json())

        # get info about project
        p = self.app.get(f"/api/projects/{TEST_PROJECT_1}")
        j = p.get_json()
        self.assertTrue("crs" in j)
        self.assertTrue("creation_datetime" in j)
        self.assertEqual(j["author"], "pblottiere")
        self.assertEqual(j["storage"], "filesystem")
        self.assertFalse("schema" in j)

        # remove last project
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_1}")

    def test_vector_symbology_line(self):
        # access symbol properties
        p = self.app.get(
            "/api/symbology/vector/line/single_symbol/line/properties"
        )
        j = p.get_json()
        self.assertTrue("line_width" in j)

    def test_vector_symbology_fill(self):
        # list symbology for fill geometries
        p = self.app.get(
            "/api/symbology/vector/polygon/single_symbol/fill/properties"
        )
        j = p.get_json()
        self.assertTrue("outline_style" in j)

    def test_vector_symbology_marker(self):
        # list symbology for marker geometries
        p = self.app.get(
            "/api/symbology/vector/point/single_symbol/marker/properties"
        )
        j = p.get_json()
        self.assertTrue("outline_style" in j)

    def test_vector_symbology_rendering(self):
        p = self.app.get("/api/symbology/vector/rendering/properties")
        j = p.get_json()
        self.assertTrue("opacity" in j)

    def test_raster_symbology_rendering(self):
        p = self.app.get("/api/symbology/raster/rendering/properties")
        j = p.get_json()
        self.assertTrue("gamma" in j)
        self.assertTrue("brightness" in j)
        self.assertTrue("contrast" in j)
        self.assertTrue("saturation" in j)

    def test_raster_symbology_singlebandgray(self):
        p = self.app.get("/api/symbology/raster/singlebandgray/properties")
        j = p.get_json()
        self.assertTrue("gray" in j)
        self.assertTrue("contrast_enhancement" in j)

    def test_raster_symbology_multibandcolor(self):
        p = self.app.get("/api/symbology/raster/multibandcolor/properties")
        j = p.get_json()
        self.assertTrue("contrast_enhancement" in j)

    def test_layers(self):
        # add project
        data = {}
        data["name"] = TEST_PROJECT_0
        data["author"] = "pblottiere"
        p = self.app.post("/api/projects/", data)
        self.assertEqual(p.status_code, 201)

        # 0 layer
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers")
        self.assertEqual(p.get_json(), [])

        # add layer
        data = {}
        data["name"] = "layer0"
        data["datasource"] = f"{GPKG}|layername=polygons"
        data["crs"] = 4326
        data["type"] = "vector"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertEqual(p.status_code, 201)

        data = {}
        data["name"] = "layer1"
        data["datasource"] = f"{GPKG}|layername=lines"
        # data["crs"] = 4326  # No CRS because it's optional
        data["type"] = "vector"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertEqual(p.status_code, 201)

        data = {}
        data["name"] = "layer2"
        data["datasource"] = f"{GPKG}|layername=points"
        data["crs"] = 4326
        data["type"] = "vector"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertEqual(p.status_code, 201)

        data = {}
        data["name"] = "layer3"
        data["datasource"] = f"{GEOTIFF}"
        data["crs"] = 4326
        data["type"] = "raster"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertEqual(p.status_code, 201)

        # 3 layers
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers")
        self.assertEqual(
            p.get_json(), ["layer0", "layer1", "layer2", "layer3"]
        )

        # layer metadata
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers/layer1")
        j = p.get_json()
        self.assertEqual(j["type"], "vector")

        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers/layer2")
        j = p.get_json()
        self.assertEqual(j["valid"], True)

        # remove layer0
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}/layers/layer0")
        self.assertEqual(p.status_code, 201)

        # 2 layer
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers")
        self.assertEqual(p.get_json(), ["layer1", "layer2", "layer3"])

        # remove last project
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}")

    def test_raster_style(self):
        # add project
        data = {}
        data["name"] = TEST_PROJECT_0
        data["author"] = "pblottiere"
        p = self.app.post("/api/projects/", data)
        self.assertEqual(p.status_code, 201)

        # 0 style
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles")
        self.assertEqual(p.get_json(), [])

        # add multibandcolor style to project
        data = {}
        data["type"] = "raster"
        data["name"] = "style_multibandcolor"
        data["symbology"] = {"type": "multibandcolor"}
        data["symbology"]["properties"] = {
            "red": {"band": 1},
            "blue": {"band": 1},
            "green": {"band": 1},
        }
        data["rendering"] = {
            "brightness": 10,
            "gamma": 1.0,
            "contrast": 3,
            "saturation": 2,
        }
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/styles", data)
        self.assertEqual(p.status_code, 201)

        p = self.app.get(
            f"/api/projects/{TEST_PROJECT_0}/styles/style_multibandcolor"
        )
        self.assertTrue("rendering" in p.get_json())
        self.assertTrue("symbology" in p.get_json())
        self.assertTrue("properties" in p.get_json()["symbology"])

        # 1 style
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles")
        self.assertTrue("style_multibandcolor" in p.get_json())

        # add raster layer
        data = {}
        data["name"] = "layer0"
        data["datasource"] = f"{GEOTIFF}"
        data["crs"] = 4326
        data["type"] = "raster"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertEqual(p.status_code, 201)

        # update layer's style
        data = {}
        data["current"] = True
        data["name"] = "style_multibandcolor"
        p = self.app.post(
            f"/api/projects/{TEST_PROJECT_0}/layers/layer0/style", data
        )
        self.assertEqual(p.status_code, 201)

        # check style for layers
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers/layer0")
        j = p.get_json()
        self.assertEqual(j["styles"], ["default", "style_multibandcolor"])
        self.assertEqual(j["current_style"], "style_multibandcolor")

        # remove style
        p = self.app.delete(
            f"/api/projects/{TEST_PROJECT_0}/styles/style_multibandcolor"
        )
        self.assertEqual(p.status_code, 415)  # style still in use

        # update layer's style
        data = {}
        data["current"] = True
        data["name"] = "default"
        p = self.app.post(
            f"/api/projects/{TEST_PROJECT_0}/layers/layer0/style", data
        )
        self.assertEqual(p.status_code, 201)

        # remove style
        p = self.app.delete(
            f"/api/projects/{TEST_PROJECT_0}/styles/style_multibandcolor"
        )
        self.assertEqual(p.status_code, 201)

        # 0 style
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles")
        self.assertEqual(p.get_json(), [])

        # remove last project
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}")

    def test_vector_style(self):
        # add project
        data = {}
        data["name"] = TEST_PROJECT_0
        data["author"] = "pblottiere"
        p = self.app.post("/api/projects/", data)
        self.assertEqual(p.status_code, 201)

        # 0 style
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles")
        self.assertEqual(p.get_json(), [])

        # add line style to project
        data = {}
        data["type"] = "vector"
        data["name"] = "style_line"
        data["symbology"] = {"type": "single_symbol", "symbol": "line"}
        data["symbology"]["properties"] = {"line_width": 0.5}
        data["rendering"] = {"opacity": 0.4}
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/styles", data)
        self.assertEqual(p.status_code, 201)

        # add fill style to project
        data = {}
        data["type"] = "vector"
        data["name"] = "style_fill"
        data["symbology"] = {"type": "single_symbol", "symbol": "fill"}
        data["symbology"]["properties"] = {"outline_width": 0.5}
        data["rendering"] = {}
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/styles", data)
        self.assertEqual(p.status_code, 201)

        # 2 styles
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles")
        self.assertTrue("style_line" in p.get_json())
        self.assertTrue("style_fill" in p.get_json())

        # style line metadata
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles/style_line")
        j = p.get_json()
        self.assertTrue(j["symbology"]["properties"]["line_width"], 0.75)

        # style fill metadata
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles/style_fill")
        j = p.get_json()
        self.assertTrue(j["symbology"]["properties"]["outline_width"], 0.75)

        # add layers
        data = {}
        data["name"] = "layer0"
        data["datasource"] = f"{GPKG}|layername=polygons"
        data["crs"] = 4326
        data["type"] = "vector"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertEqual(p.status_code, 201)

        data = {}
        data["name"] = "layer1"
        data["datasource"] = f"{GPKG}|layername=lines"
        data["crs"] = 32637
        data["type"] = "vector"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertEqual(p.status_code, 201)

        # add style to layers
        data = {}
        data["current"] = False
        data["name"] = "style_fill"
        p = self.app.post(
            f"/api/projects/{TEST_PROJECT_0}/layers/layer0/style", data
        )
        self.assertEqual(p.status_code, 201)

        data = {}
        data["current"] = True
        data["name"] = "style_line"
        p = self.app.post(
            f"/api/projects/{TEST_PROJECT_0}/layers/layer1/style", data
        )
        self.assertEqual(p.status_code, 201)

        # check style for layers
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers/layer0")
        j = p.get_json()
        self.assertEqual(j["styles"], ["default", "style_fill"])
        self.assertEqual(j["current_style"], "default")

        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers/layer1")
        j = p.get_json()
        self.assertEqual(j["styles"], ["default", "style_line"])
        self.assertEqual(j["current_style"], "style_line")

        # remove style
        p = self.app.delete(
            f"/api/projects/{TEST_PROJECT_0}/styles/style_fill"
        )
        self.assertEqual(p.status_code, 201)

        # 1 style
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles")
        self.assertEqual(p.get_json(), ["style_line"])

        # remove last project
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}")

    def test_default_style(self):
        # add project
        data = {}
        data["name"] = TEST_PROJECT_0
        data["author"] = "pblottiere"
        data["storage"] = "filesystem"
        p = self.app.post("/api/projects/", data)
        self.assertEqual(p.status_code, 201)

        # default styles
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles/default")
        self.assertEqual(
            p.get_json(),
            {
                "line": "default",
                "polygon": "default",
                "point": "default",
            },
        )

        # add line style to project
        data = {}
        data["type"] = "vector"
        data["name"] = "style_line"
        data["symbology"] = {"type": "single_symbol", "symbol": "line"}
        data["symbology"]["properties"] = {
            "outline_width": 0.75,
            "outline_style": "dash",
            "customdash": "10;3",
            "use_custom_dash": "1",
            "outline_color": "#0055FF",
        }
        data["rendering"] = {}
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/styles", data)
        self.assertEqual(p.status_code, 201)

        # add fill style to project
        data = {}
        data["type"] = "vector"
        data["name"] = "style_fill"
        data["symbology"] = {"type": "single_symbol", "symbol": "fill"}
        data["symbology"]["properties"] = {
            "color": "#00BBBB",
            "style": "cross",
            "outline_width": 0.16,
            "outline_color": "#002222",
        }
        data["rendering"] = {}
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/styles", data)
        self.assertEqual(p.status_code, 201)

        # add marker style to project
        data = {}
        data["type"] = "vector"
        data["name"] = "style_marker"
        data["symbology"] = {"type": "single_symbol", "symbol": "marker"}
        data["symbology"]["properties"] = {
            "color": "#00BBBB",
            "name": "star",
            "size": 6,
            "angle": 45,
        }
        data["rendering"] = {}
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/styles", data)
        self.assertEqual(p.status_code, 201)

        # set default styles for polygons/fill symbol
        data = {}
        data["symbology"] = "single_symbol"
        data["geometry"] = "polygon"
        data["symbol"] = "fill"
        data["style"] = "style_fill"
        p = self.app.post(
            f"/api/projects/{TEST_PROJECT_0}/styles/default", data
        )
        self.assertEqual(p.status_code, 201)

        # set default styles for line/line symbol
        data = {}
        data["symbology"] = "single_symbol"
        data["geometry"] = "line"
        data["symbol"] = "line"
        data["style"] = "style_line"
        p = self.app.post(
            f"/api/projects/{TEST_PROJECT_0}/styles/default", data
        )
        self.assertEqual(p.status_code, 201)

        # set default styles for point/marker symbol
        data = {}
        data["symbology"] = "single_symbol"
        data["geometry"] = "point"
        data["symbol"] = "marker"
        data["style"] = "style_marker"
        p = self.app.post(
            f"/api/projects/{TEST_PROJECT_0}/styles/default", data
        )
        self.assertEqual(p.status_code, 201)

        # check default style
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles/default")
        self.assertEqual(
            p.get_json(),
            {
                "line": "style_line",
                "polygon": "style_fill",
                "point": "style_marker",
            },
        )

        # add layer
        data = {}
        data["name"] = "layer0"
        data["datasource"] = f"{GPKG}|layername=polygons"
        data["crs"] = 4326
        data["type"] = "vector"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertEqual(p.status_code, 201)

        data = {}
        data["name"] = "layer1"
        data["datasource"] = f"{GPKG}|layername=lines"
        data["crs"] = 4326
        data["type"] = "vector"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertEqual(p.status_code, 201)

        data = {}
        data["name"] = "layer2"
        data["datasource"] = f"{GPKG}|layername=points"
        data["crs"] = 4326
        data["type"] = "vector"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertEqual(p.status_code, 201)

        # check if default style is applied when adding a new layer in the project
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers/layer0")
        j = p.get_json()
        self.assertEqual(j["styles"], ["default", "style_fill"])
        self.assertEqual(j["current_style"], "style_fill")

        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers/layer1")
        j = p.get_json()
        self.assertEqual(j["styles"], ["default", "style_line"])
        self.assertEqual(j["current_style"], "style_line")

        if not self.app.is_flask_client:
            # save polygon layer as png
            r = self.app.get(
                f"/api/projects/{TEST_PROJECT_0}/layers/layer0/map"
            )
            with open(
                f"/tmp/{TEST_PROJECT_0}_layer0_style_fill.png", "wb"
            ) as out_file:
                out_file.write(r.resp.content)

            # save line layer as png
            r = self.app.get(
                f"/api/projects/{TEST_PROJECT_0}/layers/layer1/map"
            )
            with open(
                f"/tmp/{TEST_PROJECT_0}_layer1_style_line.png", "wb"
            ) as out_file:
                out_file.write(r.resp.content)

            # save point layer as png
            r = self.app.get(
                f"/api/projects/{TEST_PROJECT_0}/layers/layer2/map"
            )
            with open(
                f"/tmp/{TEST_PROJECT_0}_layer2_style_marker.png", "wb"
            ) as out_file:
                out_file.write(r.resp.content)

        # remove last project
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}")


if __name__ == "__main__":
    unittest.main()
