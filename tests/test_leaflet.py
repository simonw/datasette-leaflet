from datasette.app import Datasette
from datasette_leaflet import (
    DEFAULT_TILE_REFERRER_POLICY,
    extra_body_script,
    extra_template_vars,
)
import importlib.util
import pathlib
import pytest

ROOT = pathlib.Path(__file__).parent.parent


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
    "asset", ["leaflet-v1.9.4.js", "leaflet-v1.9.4.min.js", "leaflet-v1.9.4.css"]
)
async def test_static_assets(datasette, asset):
    path = "/-/static-plugins/datasette-leaflet/{}".format(asset)
    assert (await datasette.client.get(path)).status_code == 200


def test_extra_template_vars(datasette):
    assert extra_template_vars(datasette) == {
        "datasette_leaflet_url": "/-/static-plugins/datasette-leaflet/leaflet-v1.9.4.js",
        "datasette_leaflet_css_url": "/-/static-plugins/datasette-leaflet/leaflet-v1.9.4.css",
    }


def test_extra_body_script(datasette):
    assert extra_body_script(datasette).strip() == (
        "window.datasette = window.datasette || {};\n"
        "datasette.leaflet = {\n"
        "    JAVASCRIPT_URL: '/-/static-plugins/datasette-leaflet/leaflet-v1.9.4.js',\n"
        "    CSS_URL: '/-/static-plugins/datasette-leaflet/leaflet-v1.9.4.css',\n"
        '    TILE_REFERRER_POLICY: "strict-origin-when-cross-origin"\n'
        "};"
    )


@pytest.mark.parametrize(
    "config,expected",
    (
        ({}, '"strict-origin-when-cross-origin"'),
        ({"tile_referrer_policy": None}, '"strict-origin-when-cross-origin"'),
        ({"tile_referrer_policy": "origin"}, '"origin"'),
        ({"tile_referrer_policy": False}, "false"),
        ({"tile_referrer_policy": "</script>"}, '"\\u003c/script>"'),
    ),
)
def test_tile_referrer_policy_setting(config, expected):
    datasette = Datasette(
        [], memory=True, metadata={"plugins": {"datasette-leaflet": config}}
    )
    assert "    TILE_REFERRER_POLICY: {}\n".format(expected) in extra_body_script(
        datasette
    )


@pytest.mark.parametrize("asset", ["leaflet-v1.9.4.js", "leaflet-v1.9.4.min.js"])
def test_bundled_javascript_sets_default_tile_referrer_policy(asset):
    # update_leaflet.py appends this to both builds, as a fallback for when
    # datasette.leaflet.TILE_REFERRER_POLICY has not been set by the plugin
    js = (ROOT / "datasette_leaflet" / "static" / asset).read_text()
    assert (
        'policy === undefined ? "{}" : policy'.format(DEFAULT_TILE_REFERRER_POLICY)
        in js
    )


def test_update_leaflet_uses_the_same_default():
    spec = importlib.util.spec_from_file_location(
        "update_leaflet", ROOT / "update_leaflet.py"
    )
    update_leaflet = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(update_leaflet)
    assert update_leaflet.DEFAULT_TILE_REFERRER_POLICY == DEFAULT_TILE_REFERRER_POLICY
