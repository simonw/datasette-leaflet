#!/usr/bin/env python3
"""Download and bundle a version of Leaflet into datasette_leaflet/static/.

Usage:
    python update_leaflet.py [VERSION]

Defaults to the version in DEFAULT_VERSION. This fetches the official Leaflet
distribution from unpkg, drops the files into the plugin's static directory
using the ``leaflet-vVERSION.*`` naming convention, refreshes the marker
images and bundled LICENSE, and removes any previously bundled version.

After running, update JS_FILE / CSS_FILE in datasette_leaflet/__init__.py and
the version strings in tests/test_datasette_leaflet.py to match.
"""
import pathlib
import sys
import urllib.request

DEFAULT_VERSION = "1.9.4"

HERE = pathlib.Path(__file__).parent
STATIC = HERE / "datasette_leaflet" / "static"
IMAGES = STATIC / "images"

IMAGE_FILES = [
    "layers-2x.png",
    "layers.png",
    "marker-icon-2x.png",
    "marker-icon.png",
    "marker-shadow.png",
]


def fetch(url):
    print("Fetching {}".format(url))
    with urllib.request.urlopen(url) as response:
        return response.read()


def strip_sourcemap(text):
    # We don't ship the .map files, so drop the reference to avoid 404s in devtools.
    lines = [
        line
        for line in text.splitlines()
        if not line.strip().startswith("//# sourceMappingURL=")
    ]
    return "\n".join(lines) + "\n"


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VERSION
    base = "https://unpkg.com/leaflet@{}/dist".format(version)

    # Remove any previously bundled leaflet-v*.js/.css files
    for old in list(STATIC.glob("leaflet-v*.js")) + list(STATIC.glob("leaflet-v*.css")):
        print("Removing {}".format(old.name))
        old.unlink()

    # JavaScript: leaflet-src.js is the readable build, leaflet.js is minified
    (STATIC / "leaflet-v{}.js".format(version)).write_text(
        strip_sourcemap(fetch("{}/leaflet-src.js".format(base)).decode("utf-8"))
    )
    (STATIC / "leaflet-v{}.min.js".format(version)).write_text(
        strip_sourcemap(fetch("{}/leaflet.js".format(base)).decode("utf-8"))
    )
    # CSS
    (STATIC / "leaflet-v{}.css".format(version)).write_text(
        strip_sourcemap(fetch("{}/leaflet.css".format(base)).decode("utf-8"))
    )

    # Marker images
    IMAGES.mkdir(parents=True, exist_ok=True)
    for name in IMAGE_FILES:
        (IMAGES / name).write_bytes(fetch("{}/images/{}".format(base, name)))

    # License
    (STATIC / "Leaflet-LICENSE").write_bytes(
        fetch("https://unpkg.com/leaflet@{}/LICENSE".format(version))
    )

    print(
        "\nBundled Leaflet {v}. Now update JS_FILE/CSS_FILE in "
        "datasette_leaflet/__init__.py and the version strings in the tests.".format(
            v=version
        )
    )


if __name__ == "__main__":
    main()
