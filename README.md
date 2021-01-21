# datasette-leaflet

Datasette plugin adding the Leaflet JavaScript library. **Under construction**.

In increasing number of Datasette plugins depend on the Leaflet JavaScript mapping library. They each have their own way of loading Leaflet, which could result in loading it multiple times (with multiple versions) if more than one plugin is installed.

This library is intended to solve this problem, by providing a single plugin they can all depend on that loads Leaflet in a reusable way.

Plugins that could benefit from this:

- [datasette-cluster-map](https://datasette.io/plugins/datasette-cluster-map)
- [datasette-leaflet-geojson](https://datasette.io/plugins/datasette-leaflet-geojson)
- [datasette-leaflet-freedraw](https://datasette.io/plugins/datasette-leaflet-freedraw)
