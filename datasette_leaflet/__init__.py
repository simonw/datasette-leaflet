from datasette import hookimpl
import textwrap

LEAFLET_VERSIONS = ["1.7.1", "1.8.0"]

JS_FILE = "leaflet.js"
ESM_FILE = "leaflet-src.esm.js"
CSS_FILE = "leaflet.css"


@hookimpl
def extra_template_vars(datasette):
    config = datasette.plugin_config("datasette-leaflet") or {}
    version = config.get("version", "1.8.0")
    if version not in LEAFLET_VERSIONS:
        version = "1.8.0"

    return {
        name: datasette.urls.static_plugins("datasette-leaflet", file)
        for name, file in {
            "datasette_leaflet_url": f"v{version}/{JS_FILE}",
            "datasette_leaflet_esm": f"v{version}/{ESM_FILE}",
            "datasette_leaflet_css_url": f"v{version}/{CSS_FILE}",
        }.items()
    }


@hookimpl
def extra_body_script(datasette):
    config = datasette.plugin_config("datasette-leaflet") or {}
    version = config.get("version", "1.8.0")
    if version not in LEAFLET_VERSIONS:
        version = "1.8.0"

    return textwrap.dedent(
        """
    window.datasette = window.datasette || {{}};
    datasette.leaflet = {{
        JAVASCRIPT_URL: '{}',
        JAVASCRIPT_ESM_URL: '{}',
        CSS_URL: '{}'
    }};
    """.format(
            datasette.urls.static_plugins("datasette-leaflet", f"v{version}/{JS_FILE}"),
            datasette.urls.static_plugins(
                "datasette-leaflet", f"v{version}/{ESM_FILE}"
            ),
            datasette.urls.static_plugins(
                "datasette-leaflet", f"v{version}/{CSS_FILE}"
            ),
        )
    )
