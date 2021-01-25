from datasette.app import Datasette
from datasette_leaflet import extra_body_script, extra_template_vars
import pytest


@pytest.fixture
def datasette():
    return Datasette([], memory=True)


@pytest.mark.asyncio
async def test_plugin_is_installed(datasette):
    response = await datasette.client.get("/-/plugins.json")
    assert response.status_code == 200
    installed_plugins = {p["name"] for p in response.json()}
    assert "datasette-leaflet" in installed_plugins


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "asset", ["leaflet-v1.7.1.js", "leaflet-v1.7.1.min.js", "leaflet-v1.7.1.css"]
)
async def test_static_assets(datasette, asset):
    path = "/-/static-plugins/datasette-leaflet/{}".format(asset)
    assert (await datasette.client.get(path)).status_code == 200


def test_extra_template_vars(datasette):
    assert extra_template_vars(datasette) == {
        "datasette_leaflet_url": "/-/static-plugins/datasette-leaflet/leaflet-v1.7.1.js",
        "datasette_leaflet_css_url": "/-/static-plugins/datasette-leaflet/leaflet-v1.7.1.css",
    }


def test_extra_body_script(datasette):
    assert extra_body_script(datasette).strip() == (
        "window.datasette = window.datasette || {};\n"
        "datasette.leaflet = {\n"
        "    JAVASCRIPT_URL: '/-/static-plugins/datasette-leaflet/leaflet-v1.7.1.js',\n"
        "    CSS_URL: '/-/static-plugins/datasette-leaflet/leaflet-v1.7.1.css'\n"
        "};"
    )
