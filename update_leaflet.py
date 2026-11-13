#!/usr/bin/env python3
"""Download and bundle a version of Leaflet into datasette_leaflet/static/.

Usage:
    python update_leaflet.py [VERSION]

Defaults to the version in DEFAULT_VERSION. This fetches the official Leaflet
distribution from unpkg, drops the files into the plugin's static directory
using the ``leaflet-vVERSION.*`` naming convention, refreshes the marker
images and bundled LICENSE, and removes any previously bundled version.

The JavaScript is not shipped exactly as downloaded: the ES module gains a
global ``window.L``, and both builds get a different default for the
``referrerPolicy`` tile layer option. See add_global_l() and
add_tile_referrer_policy().

After running, update JS_FILE / CSS_FILE in datasette_leaflet/__init__.py and
the version strings in tests/test_datasette_leaflet.py to match.
"""
import pathlib
import re
import sys
import urllib.request

DEFAULT_VERSION = "1.9.4"

# Keep this in sync with the constant of the same name in
# datasette_leaflet/__init__.py - a test checks that they match
DEFAULT_TILE_REFERRER_POLICY = "strict-origin-when-cross-origin"

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


def add_global_l(js):
    # The ES module build only exports names, it does not create the global L
    # that Leaflet plugins such as Leaflet.markercluster expect. Append a
    # window.L built from the export list at the end of the file, so that
    # "export { toBounds as bounds, canvas }" gives "bounds: toBounds, canvas: canvas"
    match = re.search(r"export \{([^}]*)\};?\s*$", js)
    if match is None:
        raise ValueError("Could not find the export list at the end of the ES module")
    pairs = []
    for item in match.group(1).split(","):
        local, _, exported = item.strip().partition(" as ")
        pairs.append("{}: {}".format(exported or local, local))
    return (
        js.rstrip("\n")
        + "\n\n// Added by datasette-leaflet: the ES module build does not create the\n"
        + "// global L that plugins such as Leaflet.markercluster expect\n"
        + "window.L = { "
        + ", ".join(pairs)
        + " };\n"
    )


def add_tile_referrer_policy(js):
    # Datasette serves its pages with "Referrer-Policy: no-referrer", but tile
    # servers such as tile.openstreetmap.org block requests that arrive without
    # a Referer header. Change the default of Leaflet's referrerPolicy tile
    # layer option (false in stock Leaflet) so tiles send the origin of the
    # site. This needs window.L, so it goes after add_global_l() for the ES
    # module. The policy comes from the tile_referrer_policy plugin setting,
    # which the plugin writes to datasette.leaflet.TILE_REFERRER_POLICY.
    return (
        js.rstrip("\n")
        + "\n\n// Added by datasette-leaflet: Datasette pages are served with\n"
        + '// "Referrer-Policy: no-referrer", but tile servers such as\n'
        + "// tile.openstreetmap.org block requests that have no Referer header.\n"
        + "// Tiles send the origin of this site by default - change that with the\n"
        + "// tile_referrer_policy plugin setting or the referrerPolicy layer option\n"
        + "(function () {\n"
        + "  var config = (window.datasette && window.datasette.leaflet) || {};\n"
        + "  var policy = config.TILE_REFERRER_POLICY;\n"
        + "  window.L.TileLayer.mergeOptions({\n"
        + "    referrerPolicy:\n"
        + '      policy === undefined ? "'
        + DEFAULT_TILE_REFERRER_POLICY
        + '" : policy\n'
        + "  });\n"
        + "})();\n"
    )


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VERSION
    base = "https://unpkg.com/leaflet@{}/dist".format(version)

    # Remove any previously bundled leaflet-v*.js/.css files
    for old in list(STATIC.glob("leaflet-v*.js")) + list(STATIC.glob("leaflet-v*.css")):
        print("Removing {}".format(old.name))
        old.unlink()

    # JavaScript. The main file is the ES module build so it can be loaded with
    # a dynamic `import()` (see README) - leaflet-src.esm.js ends in `export {}`.
    # add_global_l() makes importing it set window.L as well.
    # leaflet.js is the minified UMD/global build for plain `<script>` use.
    # Both get the datasette-leaflet default for the tile referrer policy.
    (STATIC / "leaflet-v{}.js".format(version)).write_text(
        add_tile_referrer_policy(
            add_global_l(
                strip_sourcemap(
                    fetch("{}/leaflet-src.esm.js".format(base)).decode("utf-8")
                )
            )
        )
    )
    (STATIC / "leaflet-v{}.min.js".format(version)).write_text(
        add_tile_referrer_policy(
            strip_sourcemap(fetch("{}/leaflet.js".format(base)).decode("utf-8"))
        )
    )
    # CSS
    (STATIC / "leaflet-v{}.css".format(version)).write_text(
        strip_sourcemap(fetch("{}/leaflet.css".format(base)).decode("utf-8"))
    )

    # Marker images
    IMAGES.mkdir(parents=True, exist_ok=True)
    for name in IMAGE_FILES:
        (IMAGES / name).write_bytes(fetch("{}/images/{}".format(base, name)))

    # License - fetched from the matching tag in the Leaflet source repo
    (STATIC / "Leaflet-LICENSE").write_bytes(
        fetch(
            "https://raw.githubusercontent.com/Leaflet/Leaflet/refs/tags/v{}/LICENSE".format(
                version
            )
        ).replace(b"\r\n", b"\n")  # The tagged file has CRLF line endings
    )

    print(
        "\nBundled Leaflet {v}. Now update JS_FILE/CSS_FILE in "
        "datasette_leaflet/__init__.py and the version strings in the tests.".format(
            v=version
        )
    )


if __name__ == "__main__":
    main()
