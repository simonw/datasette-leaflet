from datasette import hookimpl
import textwrap

JS_FILE = "leaflet-v1.7.1.js"
CSS_FILE = "leaflet-v1.7.1.css"


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
        CSS_URL: '{}'
    }};
    """.format(
            datasette.urls.static_plugins("datasette-leaflet", JS_FILE),
            datasette.urls.static_plugins("datasette-leaflet", CSS_FILE),
        )
    )
