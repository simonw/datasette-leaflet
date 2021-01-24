from datasette import hookimpl


@hookimpl
def extra_template_vars(datasette):
    return {
        name: datasette.urls.static_plugins("datasette-leaflet", file)
        for name, file in {
            "datasette_leaflet_url": "leaflet-v1.7.1.js",
            "datasette_leaflet_css_url": "leaflet-v1.7.1.css",
        }.items()
    }
