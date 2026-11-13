try:
    from playwright import sync_api
except ImportError:
    sync_api = None
import pytest
pytestmark = pytest.mark.skipif(sync_api is None, reason="playwright not installed")


def test_datasette_leaflet_urls_are_injected(ds_server, page):
    # datasette.leaflet.JAVASCRIPT_URL / CSS_URL should be injected on every page
    page.goto(ds_server + "/")
    urls = page.evaluate("() => window.datasette.leaflet")
    assert urls["JAVASCRIPT_URL"].endswith("/leaflet-v1.9.4.js")
    assert urls["CSS_URL"].endswith("/leaflet-v1.9.4.css")


def test_javascript_url_can_be_imported_as_a_module(ds_server, page):
    # This is the documented usage - the bundled JS must be an ES module so that
    # `import(datasette.leaflet.JAVASCRIPT_URL)` resolves to the Leaflet exports.
    page.goto(ds_server + "/")
    result = page.evaluate(
        """async () => {
            const leaflet = await import(window.datasette.leaflet.JAVASCRIPT_URL);
            return {
                version: leaflet.version,
                map: typeof leaflet.map,
                tileLayer: typeof leaflet.tileLayer,
            };
        }"""
    )
    assert result["version"] == "1.9.4"
    assert result["map"] == "function"
    assert result["tileLayer"] == "function"


def test_importing_the_module_sets_a_global_l(ds_server, page):
    # Leaflet plugins such as Leaflet.markercluster expect a global L which
    # they can add their own classes to - the ES module build of Leaflet does
    # not create one, so update_leaflet.py appends a window.L to the file
    page.goto(ds_server + "/")
    assert page.evaluate("() => typeof window.L") == "undefined"
    result = page.evaluate(
        """async () => {
            const leaflet = await import(window.datasette.leaflet.JAVASCRIPT_URL);
            const missing = Object.keys(leaflet).filter(
                (key) => window.L[key] !== leaflet[key]
            );
            window.L.addedByPlugin = true;
            return {
                version: window.L.version,
                missing: missing,
                exportCount: Object.keys(leaflet).length,
                extensible: window.L.addedByPlugin,
            };
        }"""
    )
    assert result["version"] == "1.9.4"
    # Every export is on the global, as the same object
    assert result["exportCount"] > 50
    assert result["missing"] == []
    assert result["extensible"] is True
