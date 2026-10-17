# Iași neighborhood place catalog: source and license

`iasi-neighborhoods.geojson` is a small derived dataset from a bounded
OpenStreetMap Overpass query saved by the local SIM mapping demonstration on
2026-10-17. It contains 24 mapped place polygons and 7 named place points. The
query covered part of the Iași metropolitan area and returned partial coverage;
it is not a complete neighborhood inventory.

The catalog metadata records the original bounded Overpass query, the Nominatim
relation used only to obtain its query bounds, the snapshot date, and tag
filters. Load the checked-in derivative with
`sim.load_neighborhood_catalog("sim/iasi-neighborhoods.geojson")`. The original
response is kept only in the ignored local demo cache; repeating the bounded
query is reproducible by method but may return a newer OSM snapshot.

The catalog is distributed under the [Open Data Commons Open Database License
(ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Attribution:
**© OpenStreetMap contributors**. See the [OpenStreetMap copyright and
license page](https://www.openstreetmap.org/copyright) and the
[ODbL legal text](https://opendatacommons.org/licenses/odbl/1-0/).

The data records preserve OSM object identifiers, source URLs, retrieval and
snapshot dates, query tags, and uncertainty notes. Source polygons are mapped
place extents and are not verified municipal or legal neighborhood boundaries.
Point-only records remain points; this catalog does not infer their boundaries.
OSM Foundation guidance describes attribution and share-alike obligations for
distributed OSM data and derivative databases; this file is therefore marked
ODbL-1.0 and kept separate from the SIM source-code license. This note is
provenance information, not legal advice.

The local raw Overpass response and geocoder response remain ignored under
`sim/.cache/local_demo/source_cache/` and are not included in the repository.
