try:
    from playwright import sync_api
except ImportError:
    sync_api = None
import base64
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


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def _tile_referers(page, server, layer_options=None):
    "Render a map on a table page, return the Referer header of each tile request"
    referers = []

    def handle(route):
        referers.append(route.request.all_headers().get("referer"))
        route.fulfill(status=200, content_type="image/png", body=PNG_1X1)

    page.route("https://tiles.example.com/**", handle)
    response = page.goto(server + "/data/places")
    # This header is why tile requests would otherwise have no Referer
    assert response.headers["referrer-policy"] == "no-referrer"
    page.evaluate(
        """async (options) => {
            const leaflet = await import(window.datasette.leaflet.JAVASCRIPT_URL);
            const div = document.createElement("div");
            div.style.width = "400px";
            div.style.height = "300px";
            document.body.appendChild(div);
            const tiles = leaflet.tileLayer(
                "https://tiles.example.com/{z}/{x}/{y}.png", options
            );
            const loaded = new Promise((resolve) => tiles.on("load", resolve));
            leaflet.map(div, {center: [0, 0], zoom: 2, layers: [tiles]});
            await loaded;
        }""",
        layer_options or {},
    )
    assert referers
    return set(referers)


def test_tiles_send_the_site_origin_as_referer(ds_server, page):
    # Just the origin, never the path of the page showing the map
    assert _tile_referers(page, ds_server) == {ds_server + "/"}


def test_referrer_policy_layer_option_overrides_the_default(ds_server, page):
    assert _tile_referers(page, ds_server, {"referrerPolicy": False}) == {None}


def test_tile_referrer_policy_setting_can_turn_it_off(
    ds_server_no_tile_referrer_policy, page
):
    page.goto(ds_server_no_tile_referrer_policy + "/")
    assert (
        page.evaluate("() => window.datasette.leaflet.TILE_REFERRER_POLICY") is False
    )
    assert _tile_referers(page, ds_server_no_tile_referrer_policy) == {None}
    # A layer can still opt back in
    assert _tile_referers(
        page, ds_server_no_tile_referrer_policy, {"referrerPolicy": "origin"}
    ) == {ds_server_no_tile_referrer_policy + "/"}


def test_default_tile_referrer_policy_is_inherited_by_wms_layers(ds_server, page):
    page.goto(ds_server + "/")
    assert page.evaluate(
        """async () => {
            const leaflet = await import(window.datasette.leaflet.JAVASCRIPT_URL);
            return [
                leaflet.TileLayer.prototype.options.referrerPolicy,
                leaflet.TileLayer.WMS.prototype.options.referrerPolicy,
            ];
        }"""
    ) == ["strict-origin-when-cross-origin"] * 2


def test_minified_build_has_the_same_tile_referrer_policy(ds_server, page):
    # leaflet-vX.min.js is the build for use in a plain <script> element
    page.goto(ds_server + "/")
    assert (
        page.evaluate(
            """() => new Promise((resolve, reject) => {
            const script = document.createElement("script");
            script.src = window.datasette.leaflet.JAVASCRIPT_URL.replace(
                /\\.js$/, ".min.js"
            );
            script.onload = () => resolve(
                window.L.TileLayer.prototype.options.referrerPolicy
            );
            script.onerror = reject;
            document.head.appendChild(script);
        })"""
        )
        == "strict-origin-when-cross-origin"
    )
