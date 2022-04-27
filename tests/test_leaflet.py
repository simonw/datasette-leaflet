from datasette.app import Datasette
from datasette_leaflet import extra_body_script, extra_template_vars, LEAFLET_VERSIONS
import pytest

FILES = ["leaflet.js", "leaflet.css"]

NAME = "datasette-leaflet"


@pytest.fixture(params=[None] + LEAFLET_VERSIONS)
def datasette(request):
    metadata = {}
    if request.param is not None:
        metadata = {"plugins": {NAME: {"version": request.param}}}
    return Datasette([], memory=True, metadata=metadata)


@pytest.mark.asyncio
async def test_plugin_is_installed(datasette):
    response = await datasette.client.get("/-/plugins.json")
    assert response.status_code == 200
    installed_plugins = {p["name"] for p in response.json()}
    assert NAME in installed_plugins


@pytest.mark.asyncio
@pytest.mark.parametrize(
    # "asset", ["leaflet-v1.7.1.js", "leaflet-v1.7.1.min.js", "leaflet-v1.7.1.css"]
    "version",
    LEAFLET_VERSIONS,
)
async def test_static_assets(datasette, version):
    for filename in FILES:
        path = f"/-/static-plugins/datasette-leaflet/v{version}/{filename}"
        assert (await datasette.client.get(path)).status_code == 200


def test_extra_template_vars(datasette):
    config = datasette.plugin_config(NAME) or {}
    version = config.get("version", "1.8.0")
    assert extra_template_vars(datasette) == {
        "datasette_leaflet_url": f"/-/static-plugins/datasette-leaflet/v{version}/leaflet.js",
        "datasette_leaflet_css_url": f"/-/static-plugins/datasette-leaflet/v{version}/leaflet.css",
    }


def test_extra_body_script(datasette):
    config = datasette.plugin_config(NAME) or {}
    version = config.get("version", "1.8.0")
    assert extra_body_script(datasette).strip() == (
        "window.datasette = window.datasette || {};\n"
        "datasette.leaflet = {\n"
        f"    JAVASCRIPT_URL: '/-/static-plugins/datasette-leaflet/v{version}/leaflet.js',\n"
        f"    CSS_URL: '/-/static-plugins/datasette-leaflet/v{version}/leaflet.css'\n"
        "};"
    )
