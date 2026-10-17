# Spatial analysis and simulation status

Updated: 2026-10-17

## Working

- Bounded Polygon, MultiPolygon, GeoJSON, GeoDataFrame, and bbox validation; 5 km² / 5 km defaults; metric UTM working CRS and WGS84 GeoJSON output.
- Cached OSMnx acquisition for walking, cycling, and driving modes, plus tagged infrastructure/POI layers with per-layer availability, retrieval metadata, and explicit OSM coverage limitations.
- Graph normalization, connected components, weighted routes, route detour ratios, walking/cycling access estimates, stable evidence-backed connectivity/access/detour issues, and heatmap-ready GeoJSON.
- Isolated pedestrian-connection scenarios with endpoint snapping, validation, Before/After path calculation, and baseline immutability.
- Offline engine tests: 9 passed. Existing `sim.smoke_test` passed on Windows with Python 3.12, OSMnx 2.1.1, NetworkX 3.7, GeoPandas 1.2.0, and Shapely 2.2.0.

## Verified real Iași snapshot

Area: `[27.5755, 47.1610, 27.5825, 47.1655]` (central Iași, about 0.26 km²); working CRS EPSG:32635. OSM snapshot retrieval completed on 2026-10-17 and is cached locally under the ignored `sim/.cache/osm/` directory.

- Walking graph: 136 nodes, 354 directed edges, 3 weak components, 131 nodes in the largest component; 107 graph nodes lie inside the study polygon.
- Driving graph: 40 nodes, 78 directed edges, 1 weak component; 24 graph nodes lie inside the study polygon.
- Returned tagged features: 151 roads, 88 walking-infrastructure features, 17 crossings, 275 buildings, 4 schools, 3 healthcare features, 9 supported services, 3 public-transport features, 8 parking features, and 5 green-space features. No explicit cycling-infrastructure features were returned; that does not establish absence.
- At the configured 15-minute / 1.3 m/s walking assumption, 105 of 107 in-area graph nodes are within threshold for each analyzed target group. Median route detour ratios: schools 1.04, healthcare 1.31, services 1.32, public transport 1.64, green space 1.41.
- The analysis generated two disconnected-component issue records and access/detour issue groups for mapped target categories. Metrics are based on mapped network nodes, not residents.
- A real graph-only intervention between OSM nodes `641092475` and `12079937967` reduced the weighted route from 648.7 m to 34.4 m (delta −614.3 m). No construction feasibility was assessed.

The default Overpass endpoint returned a capacity-related 502 for some requests. A listed alternate endpoint supplied the successful feature snapshot. Further bike-network acquisition remained slow and was stopped after the walking and driving snapshots were cached; the bike graph has not been verified against live OSM in this run.

## In progress / next

- Verify a live cycling graph on a future bounded request; currently no explicit cycleway features were returned in the study snapshot.
- Add a real OSM-to-SUMO conversion and a clearly labeled deterministic synthetic-demand run only when the geospatial graph pipeline is stable.
- Add population-weighted accessibility only when a suitable, licensed population/address dataset is available.

## Limitations

- OSM geometry, tags, and coverage are incomplete and change over time. Empty layers remain unknown rather than proof of nonexistence.
- Walking/cycling travel times use constant speed assumptions. Population, congestion, observed traffic volumes, and real-time conditions are not inferred.
- Interventions are hypothetical graph links; physical safety, grade, legal status, ownership, and buildability are outside the model.
- SUMO discovery/smoke support is preserved. Real-area network conversion and calibrated traffic simulation are not implemented.
- The `uv` executable is not available in this Windows environment. The project's existing `.venv` matched the locked geospatial package versions and was used for targeted tests without installing dependencies.
