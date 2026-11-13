from datasette import hookimpl
import json
import textwrap

JS_FILE = "leaflet-v1.9.4.js"
CSS_FILE = "leaflet-v1.9.4.css"

# Datasette serves pages with "Referrer-Policy: no-referrer", but tile servers
# such as tile.openstreetmap.org block requests that have no Referer header.
# The bundled Leaflet uses this as the default referrerPolicy for tile layers,
# which sends the origin of the site to the tile server but never the full URL.
DEFAULT_TILE_REFERRER_POLICY = "strict-origin-when-cross-origin"


def tile_referrer_policy(datasette):
    "The tile_referrer_policy plugin setting: a policy string, or False for none"
    config = datasette.plugin_config("datasette-leaflet") or {}
    policy = config.get("tile_referrer_policy")
    if policy is None:
        return DEFAULT_TILE_REFERRER_POLICY
    return policy


@hookimpl
def extra_template_vars(datasette):
    return {
        name: datasette.urls.static_plugins("datasette-leaflet", file)
        for name, file in {
            "datasette_leaflet_url": JS_FILE,
            "datasette_leaflet_css_url": CSS_FILE,
        }.items()
    }


@hookimpl
def extra_body_script(datasette):
    return textwrap.dedent(
        """
    window.datasette = window.datasette || {{}};
    datasette.leaflet = {{
        JAVASCRIPT_URL: '{}',
        CSS_URL: '{}',
        TILE_REFERRER_POLICY: {}
    }};
    """.format(
            datasette.urls.static_plugins("datasette-leaflet", JS_FILE),
            datasette.urls.static_plugins("datasette-leaflet", CSS_FILE),
            # < is escaped so the value cannot close the <script> element
            json.dumps(tile_referrer_policy(datasette)).replace("<", "\\u003c"),
        )
    )
