"""Bounded, cached OpenStreetMap acquisition for ARTERIA."""

from __future__ import annotations

import hashlib
import json
import math
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import geopandas as gpd
import osmnx as ox
from pyproj import CRS
from shapely.geometry import MultiPolygon, Polygon, box, mapping, shape
from shapely.geometry.base import BaseGeometry


DEFAULT_MAX_AREA_KM2 = 5.0
DEFAULT_MAX_EXTENT_KM = 5.0
SUPPORTED_MODES = ("walk", "bike", "drive")
_OSMNX_SETTINGS_LOCK = threading.Lock()

FEATURE_TAGS: dict[str, bool | str | list[str]] = {
    "highway": True,
    "cycleway": True,
    "bicycle": True,
    "foot": True,
    "crossing": True,
    "building": True,
    "amenity": [
        "school", "kindergarten", "university", "hospital", "clinic", "doctors",
        "pharmacy", "library", "community_centre", "police", "fire_station",
        "parking", "bus_station", "marketplace", "place_of_worship",
    ],
    "healthcare": True,
    "public_transport": True,
    "railway": ["station", "tram_stop", "halt", "subway_entrance"],
    "leisure": ["park", "garden", "recreation_ground", "nature_reserve"],
    "landuse": ["grass", "forest", "recreation_ground", "allotments"],
    "natural": ["wood", "grassland", "scrub"],
    "parking": True,
}

FEATURE_CATEGORY_SCHEMA_VERSION = "arteria.osm-feature-categories.v1"
FEATURE_CATEGORY_TAGS: dict[str, dict[str, bool | str | list[str]]] = {
    "buildings": {"building": True},
    "schools": {"amenity": ["kindergarten", "school", "university"]},
    "healthcare": {"amenity": ["clinic", "doctors", "hospital", "pharmacy"], "healthcare": True},
    "services": {
        "amenity": [
            "clinic", "community_centre", "doctors", "fire_station", "hospital",
            "kindergarten", "library", "marketplace", "pharmacy", "police", "school", "university",
        ],
    },
    "public_transport": {
        "amenity": ["bus_station"],
        "highway": ["bus_stop"],
        "public_transport": True,
        "railway": ["halt", "station", "subway_entrance", "tram_stop"],
    },
    "parking": {"amenity": ["parking"], "parking": True},
    "green_space": {
        "landuse": ["allotments", "forest", "grass", "recreation_ground"],
        "leisure": ["garden", "nature_reserve", "park", "recreation_ground"],
        "natural": ["grassland", "scrub", "wood"],
    },
    "crossings": {"crossing": True, "highway": ["crossing"]},
}
MAX_FEATURE_CATEGORIES = 4
MAX_OSM_FEATURE_COUNT = 5_000
MAX_OSM_FEATURE_JSON_BYTES = 4 * 1024 * 1024
FEATURE_REQUEST_TIMEOUT_SECONDS = 60
_SUPPORTED_FEATURE_GEOMETRIES = {
    "Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon",
}

LAYER_TAGS = {
    "roads": "highway",
    "walking_infrastructure": "highway / foot / crossing",
    "cycling_infrastructure": "highway / cycleway / bicycle",
    "crossings": "highway=crossing or crossing",
    "buildings": "building",
    "schools": "amenity=school|kindergarten|university",
    "healthcare": "amenity or healthcare",
    "services": "supported amenity values",
    "public_transport": "public_transport / railway / highway=bus_stop",
    "parking": "amenity=parking or parking",
    "green_space": "leisure / landuse / natural",
}


class AreaValidationError(ValueError):
    """Raised when a requested study area is invalid or exceeds query limits."""


class OSMDataError(RuntimeError):
    """Raised when none of the requested OSM networks can be acquired."""


@dataclass(frozen=True)
class StudyArea:
    polygon: Polygon | MultiPolygon
    city_id: str
    area_id: str
    boundary_source: str
    working_crs: str

    @property
    def extent(self) -> list[float]:
        return [float(value) for value in self.polygon.bounds]

    @property
    def geojson(self) -> dict[str, Any]:
        return mapping(self.polygon)


@dataclass
class OSMData:
    area: StudyArea
    graphs: dict[str, Any]
    layers: dict[str, gpd.GeoDataFrame]
    layer_availability: dict[str, dict[str, Any]]
    metadata: dict[str, Any]
    warnings: list[str]


def _get_input_geometry(area: Any) -> tuple[BaseGeometry, str, str, str, str | None]:
    city_id, area_id, boundary_source, crs = "iasi-ro", "user-selected-area", "user_selected", None
    value = area
    if isinstance(area, dict):
        city_id = str(area.get("city_id") or city_id)
        area_id = str(area.get("area_id") or area_id)
        boundary_source = str(area.get("boundary_source") or boundary_source)
        crs = area.get("crs")
        if "bbox" in area:
            value = area["bbox"]
            boundary_source = str(area.get("boundary_source") or "bounded_bbox")
        elif "boundary" in area:
            value = area["boundary"]
        elif area.get("type") == "Feature":
            value = area.get("geometry")
        elif area.get("type") in {"Polygon", "MultiPolygon"}:
            value = area

    if isinstance(value, BaseGeometry):
        geometry = value
    elif isinstance(value, (tuple, list)) and len(value) == 4 and all(
        isinstance(item, (int, float)) for item in value
    ):
        west, south, east, north = (float(item) for item in value)
        if east <= west or north <= south:
            raise AreaValidationError("Bounding box must be ordered west, south, east, north.")
        geometry = box(west, south, east, north)
        boundary_source = "bounded_bbox"
    elif isinstance(value, dict) and value.get("type") in {"Polygon", "MultiPolygon"}:
        geometry = shape(value)
    elif hasattr(value, "geometry") and hasattr(value, "crs"):
        if value.crs is None:
            raise AreaValidationError("Input GeoDataFrame must have a declared CRS.")
        projected = value.to_crs("EPSG:4326")
        geometry = projected.geometry.union_all()
        crs = "EPSG:4326"
    else:
        raise AreaValidationError("Area must be a Polygon, MultiPolygon, GeoJSON feature, or [west, south, east, north] bounding box.")

    if crs and not isinstance(area, BaseGeometry):
        try:
            source_crs = CRS.from_user_input(crs)
        except Exception as error:
            raise AreaValidationError(f"Invalid area CRS: {crs!r}.") from error
        if source_crs.to_epsg() != 4326:
            if hasattr(value, "to_crs"):
                geometry = value.to_crs("EPSG:4326").geometry.union_all()
            else:
                raise AreaValidationError("GeoJSON and bounding-box coordinates must use EPSG:4326.")
    return geometry, city_id, area_id, boundary_source, crs


def normalize_area(
    area: Any,
    *,
    max_area_km2: float = DEFAULT_MAX_AREA_KM2,
    max_extent_km: float = DEFAULT_MAX_EXTENT_KM,
) -> StudyArea:
    """Validate an EPSG:4326 polygon/bbox and choose a local metric CRS."""
    if isinstance(area, StudyArea):
        return area
    if max_area_km2 <= 0 or max_extent_km <= 0:
        raise AreaValidationError("Area limits must be positive.")
    geometry, city_id, area_id, boundary_source, _ = _get_input_geometry(area)
    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise AreaValidationError("Study area must be a Polygon or MultiPolygon.")
    if geometry.is_empty or not geometry.is_valid:
        raise AreaValidationError("Study area must be non-empty and topologically valid.")
    west, south, east, north = geometry.bounds
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise AreaValidationError("Study area coordinates must be longitude/latitude in EPSG:4326 bounds.")

    geographic = gpd.GeoSeries([geometry], crs="EPSG:4326")
    working_crs = geographic.estimate_utm_crs()
    if working_crs is None:
        raise AreaValidationError("Could not determine a suitable local metric CRS for this area.")
    metric = geographic.to_crs(working_crs).iloc[0]
    if metric.area <= 0 or metric.area > max_area_km2 * 1_000_000:
        raise AreaValidationError(f"Study area must be greater than zero and no larger than {max_area_km2:g} km².")
    min_x, min_y, max_x, max_y = metric.bounds
    if max(max_x - min_x, max_y - min_y) > max_extent_km * 1000:
        raise AreaValidationError(f"Study area extent must not exceed {max_extent_km:g} km in either dimension.")
    return StudyArea(
        polygon=geometry,
        city_id=city_id,
        area_id=area_id,
        boundary_source=boundary_source,
        working_crs=working_crs.to_string(),
    )


def _area_key(area: StudyArea) -> str:
    payload = area.polygon.normalize().wkb + json.dumps(
        {"feature_tags": FEATURE_TAGS, "osmnx_version": ox.__version__},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:20]


def _source_area_geometry_hash(area: StudyArea) -> str:
    """Hash the canonical WGS84 boundary independently of query configuration."""
    return hashlib.sha256(area.polygon.normalize().wkb).hexdigest()


def _source_area_metadata(area: StudyArea) -> dict[str, Any]:
    """Describe the exact requested geometry for newly written cache sidecars."""
    return {
        "city_id": area.city_id,
        "area_id": area.area_id,
        "boundary_source": area.boundary_source,
        "source_area_geometry": mapping(area.polygon.normalize()),
        "source_area_geometry_sha256": _source_area_geometry_hash(area),
        "source_area_crs": "EPSG:4326",
        "working_crs": area.working_crs,
    }


def _normalize_feature_categories(
    categories: Sequence[str] | None,
    *,
    include_features: bool,
) -> tuple[str, ...] | None:
    if categories is None:
        return None
    if isinstance(categories, str):
        raise ValueError("feature_categories must be a sequence of supported category IDs, not a string.")
    try:
        values = tuple(categories)
    except TypeError as error:
        raise ValueError("feature_categories must be a sequence of supported category IDs.") from error
    if any(not isinstance(value, str) or not value for value in values):
        raise ValueError("feature_categories must contain non-empty string category IDs.")
    if len(values) != len(set(values)):
        raise ValueError("feature_categories must not contain duplicate category IDs.")
    if len(values) > MAX_FEATURE_CATEGORIES:
        raise ValueError(f"feature_categories may contain at most {MAX_FEATURE_CATEGORIES} categories.")
    unsupported = sorted(set(values) - FEATURE_CATEGORY_TAGS.keys())
    if unsupported:
        raise ValueError(f"Unsupported OSM feature category IDs: {unsupported!r}. Supported categories are {tuple(FEATURE_CATEGORY_TAGS)}.")
    if not include_features and values:
        raise ValueError("include_features=False conflicts with a non-empty feature_categories selection.")
    return tuple(sorted(values))


def _feature_query_tags(categories: Sequence[str]) -> dict[str, bool | str | list[str]]:
    merged: dict[str, bool | str | list[str]] = {}
    for category in categories:
        for key, value in FEATURE_CATEGORY_TAGS[category].items():
            current = merged.get(key)
            if value is True or current is True:
                merged[key] = True
                continue
            values = set(current if isinstance(current, list) else ([current] if isinstance(current, str) else []))
            values.update(value if isinstance(value, list) else [value])
            merged[key] = sorted(values)
    return {key: merged[key] for key in sorted(merged)}


def _feature_cache_identity(
    area: StudyArea,
    area_key: str,
    categories: Sequence[str] | None,
    query_tags: dict[str, bool | str | list[str]],
) -> str:
    if categories is None:
        # Preserve the historical filename and lookup path for the broad query.
        return area_key
    payload = {
        "area_geometry_sha256": _source_area_geometry_hash(area),
        "categories": list(categories),
        "query_tags": query_tags,
        "schema_version": FEATURE_CATEGORY_SCHEMA_VERSION,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:20]


def _clean_feature_frame(raw: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, int]:
    frame = _feature_frame(raw)
    valid_rows = []
    for index, geometry in frame.geometry.items():
        try:
            if geometry is None or geometry.is_empty or not geometry.is_valid or geometry.geom_type not in _SUPPORTED_FEATURE_GEOMETRIES:
                continue
            bounds = tuple(float(value) for value in geometry.bounds)
            if len(bounds) != 4 or not all(math.isfinite(value) for value in bounds):
                continue
            if bounds[0] < -180 or bounds[2] > 180 or bounds[1] < -90 or bounds[3] > 90:
                continue
        except Exception:
            continue
        valid_rows.append(index)
    rejected = len(frame) - len(valid_rows)
    return frame.loc[valid_rows].copy().reset_index(drop=True), rejected


def _serialized_feature_frame(frame: gpd.GeoDataFrame) -> str:
    return frame.to_json(to_wgs84=True, drop_id=True, na="null", default=_json_default)


def _load_verified_feature_cache(
    path: Path,
    *,
    area: StudyArea,
    area_key: str,
    categories: Sequence[str] | None,
    query_tags: dict[str, bool | str | list[str]],
) -> tuple[gpd.GeoDataFrame, dict[str, Any], str]:
    sidecar = _network_metadata_path(path)
    if not sidecar.is_file():
        raise ValueError("feature cache metadata is missing; source area cannot be verified")
    metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    geometry_hash = _source_area_geometry_hash(area)
    cached_hash = metadata.get("source_area_geometry_sha256")
    if cached_hash:
        if cached_hash != geometry_hash:
            raise ValueError("feature cache source geometry hash does not match the requested area")
        verification = "geometry_sha256"
    elif categories is None and metadata.get("area_key") == area_key:
        verification = "matching_legacy_area_key"
    else:
        raise ValueError("feature cache has no verifiable source geometry metadata")
    if metadata.get("area_key") != area_key:
        raise ValueError("feature cache area key does not match the requested area")
    if categories is None:
        if metadata.get("query", {}).get("tags") != FEATURE_TAGS:
            raise ValueError("legacy feature cache tag query does not match the current broad query")
    else:
        if metadata.get("category_schema_version") != FEATURE_CATEGORY_SCHEMA_VERSION:
            raise ValueError("feature cache category schema does not match")
        if metadata.get("feature_categories") != list(categories) or metadata.get("query", {}).get("tags") != query_tags:
            raise ValueError("feature cache category selection or tag query does not match")
    frame = _load_cached_frame(path)
    if len(frame) > MAX_OSM_FEATURE_COUNT:
        raise ValueError("feature cache exceeds the configured feature-count bound")
    cleaned, rejected = _clean_feature_frame(frame)
    if rejected:
        raise ValueError(f"feature cache contains {rejected} invalid or out-of-range geometries")
    if len(_serialized_feature_frame(cleaned).encode("utf-8")) > MAX_OSM_FEATURE_JSON_BYTES:
        raise ValueError("feature cache exceeds the configured serialized-output bound")
    return cleaned, metadata, verification


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _feature_frame(raw: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    frame = raw.copy()
    index_frame = frame.index.to_frame(index=False)
    for column in index_frame.columns:
        normalized_name = {"element": "osm_element_type", "osmid": "osm_id"}.get(column, f"osm_{column}")
        if normalized_name not in frame.columns:
            frame[normalized_name] = index_frame[column].to_numpy()
    frame = frame.reset_index(drop=True)
    if "osm_id" in frame:
        frame["osm_id"] = frame["osm_id"].map(lambda value: str(value) if value is not None else None)
    if frame.crs is None:
        frame = frame.set_crs("EPSG:4326")
    else:
        frame = frame.to_crs("EPSG:4326")
    return frame


def _truthy_tag(value: Any) -> bool:
    if value is None:
        return False
    try:
        if value != value:  # pandas/numpy NaN
            return False
    except (TypeError, ValueError):
        pass
    if isinstance(value, (list, tuple, set)):
        return any(_truthy_tag(item) for item in value)
    if isinstance(value, dict):
        return bool(value)
    return str(value).strip().casefold() not in {"", "nan", "nat", "<na>", "none", "false", "no", "0"}


def _tag(row: Any, key: str) -> Any:
    try:
        return row.get(key)
    except AttributeError:
        return None


def _tag_in(value: Any, allowed: set[str]) -> bool:
    if isinstance(value, (list, tuple, set)):
        return any(_tag_in(item, allowed) for item in value)
    return _truthy_tag(value) and str(value).casefold() in allowed


def _layer_masks(features: gpd.GeoDataFrame) -> dict[str, gpd.GeoDataFrame]:
    if features.empty:
        return {name: features.copy() for name in LAYER_TAGS}
    masks: dict[str, list[bool]] = {name: [] for name in LAYER_TAGS}
    for _, row in features.iterrows():
        highway = _tag(row, "highway")
        building = _tag(row, "building")
        amenity = _tag(row, "amenity")
        healthcare = _tag(row, "healthcare")
        public_transport = _tag(row, "public_transport")
        railway = _tag(row, "railway")
        leisure = _tag(row, "leisure")
        landuse = _tag(row, "landuse")
        natural = _tag(row, "natural")
        cycling = _truthy_tag(_tag(row, "cycleway")) or _truthy_tag(_tag(row, "bicycle"))
        foot = _tag(row, "foot")
        crossing = _tag(row, "crossing")
        tags = {
            "roads": _truthy_tag(highway),
            "walking_infrastructure": _tag_in(highway, {"footway", "pedestrian", "steps", "path", "living_street", "crossing"}) or _truthy_tag(foot) or _truthy_tag(crossing),
            "cycling_infrastructure": _tag_in(highway, {"cycleway", "path", "track"}) or _truthy_tag(cycling),
            "crossings": _tag_in(highway, {"crossing"}) or _truthy_tag(crossing),
            "buildings": _truthy_tag(building),
            "schools": _tag_in(amenity, {"school", "kindergarten", "university"}),
            "healthcare": _truthy_tag(healthcare) or _tag_in(amenity, {"hospital", "clinic", "doctors", "pharmacy"}),
            "services": _tag_in(amenity, {"school", "kindergarten", "university", "hospital", "clinic", "doctors", "pharmacy", "library", "community_centre", "police", "fire_station", "marketplace"}),
            "public_transport": _truthy_tag(public_transport) or _tag_in(railway, {"station", "tram_stop", "halt", "subway_entrance"}) or _tag_in(highway, {"bus_stop"}) or _tag_in(amenity, {"bus_station"}),
            "parking": _tag_in(amenity, {"parking"}) or _truthy_tag(_tag(row, "parking")),
            "green_space": _tag_in(leisure, {"park", "garden", "recreation_ground", "nature_reserve"}) or _tag_in(landuse, {"grass", "forest", "recreation_ground", "allotments"}) or _tag_in(natural, {"wood", "grassland", "scrub"}),
        }
        for name, matches in tags.items():
            masks[name].append(matches)
    return {name: features.loc[mask].copy().reset_index(drop=True) for name, mask in masks.items()}


def _cache_frame(path: Path, frame: gpd.GeoDataFrame) -> None:
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    temporary.write_text(frame.to_json(to_wgs84=True, drop_id=True, na="null", default=_json_default), encoding="utf-8")
    temporary.replace(path)


def _load_cached_frame(path: Path) -> gpd.GeoDataFrame:
    frame = gpd.read_file(path)
    if "osm_id" in frame:
        frame["osm_id"] = frame["osm_id"].map(lambda value: str(value) if value is not None else None)
    return frame.to_crs("EPSG:4326")


def _network_metadata_path(graph_path: Path) -> Path:
    return graph_path.with_suffix(".json")


def _is_usable_network(graph: Any) -> bool:
    """A routable OSM network must contain at least one node and one edge."""
    return graph.number_of_nodes() > 0 and graph.number_of_edges() > 0


def acquire_osm_data(
    area: Any,
    *,
    modes: Iterable[str] = SUPPORTED_MODES,
    cache_dir: str | Path | None = None,
    use_cache: bool = True,
    force_refresh: bool = False,
    overpass_url: str | None = None,
    include_features: bool = True,
    feature_categories: Sequence[str] | None = None,
    max_area_km2: float = DEFAULT_MAX_AREA_KM2,
    max_extent_km: float = DEFAULT_MAX_EXTENT_KM,
) -> OSMData:
    """Download OSM features and mode-specific graphs for a bounded area.

    OSMnx's standard Overpass rate limiting remains enabled. Both OSMnx HTTP
    responses and normalized GraphML/GeoJSON snapshots are cached under sim/.cache
    by default. ``feature_categories=None`` retains the legacy broad feature query
    when ``include_features=True``. An explicit category sequence queries only
    those supported categories; ``[]`` disables feature queries. A non-empty
    category selection conflicts with ``include_features=False`` and is rejected.
    Failed modes are reported when another requested graph succeeds; an all-mode
    failure raises OSMDataError. Graph-only consumers may reuse a verified legacy
    feature cache; otherwise feature layers remain unknown.
    """
    if isinstance(modes, str):
        raise ValueError(f"modes must be a non-empty iterable of mode names from {SUPPORTED_MODES}, not a string.")
    try:
        mode_values = tuple(modes)
    except TypeError as error:
        raise ValueError(f"modes must be a non-empty iterable of mode names from {SUPPORTED_MODES}.") from error
    if not mode_values:
        raise ValueError(f"modes must be a non-empty selection from {SUPPORTED_MODES}.")
    if any(not isinstance(mode, str) or mode not in SUPPORTED_MODES for mode in mode_values):
        unsupported = [mode for mode in mode_values if not isinstance(mode, str) or mode not in SUPPORTED_MODES]
        raise ValueError(f"Unsupported OSM network mode(s): {unsupported!r}. Supported modes are {SUPPORTED_MODES}.")
    if not isinstance(include_features, bool):
        raise ValueError("include_features must be a boolean.")
    categories = _normalize_feature_categories(feature_categories, include_features=include_features)
    requested_modes = tuple(dict.fromkeys(mode_values))
    normalized = normalize_area(area, max_area_km2=max_area_km2, max_extent_km=max_extent_km)
    base = Path(cache_dir) if cache_dir else Path(__file__).resolve().parent / ".cache" / "osm"
    base.mkdir(parents=True, exist_ok=True)
    http_cache = base / "http"
    http_cache.mkdir(parents=True, exist_ok=True)
    key = _area_key(normalized)
    query_tags = FEATURE_TAGS if categories is None else _feature_query_tags(categories)
    feature_cache_key = _feature_cache_identity(normalized, key, categories, query_tags)
    feature_query_requested = include_features if categories is None else bool(categories)
    graphs: dict[str, Any] = {}
    warnings: list[str] = []
    network_retrieved: dict[str, str] = {}
    network_failures: dict[str, str] = {}
    cache_hit_modes: list[str] = []
    feature_retrieved: str | None = None
    feature_cache_hit = False
    feature_cache_status = "disabled" if not use_cache else "miss"
    feature_cache_verification = "not_checked"
    feature_request_error: str | None = None
    feature_raw_count: int | None = None
    rejected_geometry_count = 0
    feature_data_available = False
    features_path = base / f"{feature_cache_key}-features.geojson"

    settings = ox.settings
    with _OSMNX_SETTINGS_LOCK:
        previous = {
            "cache_folder": settings.cache_folder,
            "use_cache": settings.use_cache,
            "requests_timeout": settings.requests_timeout,
            "overpass_url": settings.overpass_url,
            "http_user_agent": settings.http_user_agent,
        }
        try:
            settings.cache_folder = str(http_cache)
            settings.use_cache = bool(use_cache and not force_refresh)
            settings.requests_timeout = 180
            settings.http_user_agent = "ARTERIA by ARION/0.1 (OSMnx geospatial client)"
            if overpass_url:
                settings.overpass_url = overpass_url.rstrip("/")
            for mode in requested_modes:
                graph_path = base / f"{key}-{mode}.graphml"
                graph_metadata = _network_metadata_path(graph_path)
                if use_cache and not force_refresh and graph_path.exists():
                    try:
                        cached_graph = ox.load_graphml(filepath=graph_path)
                        if not _is_usable_network(cached_graph):
                            raise ValueError("cached graph has no routable edges")
                        cached_area_key = cached_graph.graph.get("arteria_area_key")
                        if cached_area_key not in (None, key):
                            raise ValueError("cached graph belongs to a different study area")
                        cached_mode = cached_graph.graph.get("arteria_mode")
                        if cached_mode not in (None, mode):
                            raise ValueError("cached graph belongs to a different network mode")
                    except Exception as error:
                        warnings.append(f"Ignoring unreadable {mode} graph cache: {error}")
                    else:
                        graphs[mode] = cached_graph
                        network_retrieved[mode] = str(cached_graph.graph.get("arteria_retrieved_at") or "unknown")
                        if graph_metadata.exists():
                            try:
                                cached_metadata = json.loads(graph_metadata.read_text(encoding="utf-8"))
                                if cached_metadata.get("mode") not in (None, mode) or cached_metadata.get("area_key") not in (None, key):
                                    raise ValueError("cache metadata does not match the graph mode and area")
                                network_retrieved[mode] = str(cached_metadata.get("retrieved_at") or network_retrieved[mode])
                            except Exception as error:
                                warnings.append(f"Ignoring unreadable {mode} graph cache metadata: {error}")
                        cache_hit_modes.append(mode)
                        continue
                try:
                    graph = ox.graph_from_polygon(
                        normalized.polygon,
                        network_type=mode,
                        simplify=True,
                        retain_all=True,
                        truncate_by_edge=True,
                    )
                    if not _is_usable_network(graph):
                        raise ValueError("OpenStreetMap returned a graph with no routable edges")
                except Exception as error:  # upstream availability varies by area and time
                    failure = f"OpenStreetMap {mode} network request failed: {type(error).__name__}: {error}"
                    warnings.append(failure)
                    network_failures[mode] = failure
                    continue

                timestamp = _timestamp()
                graph.graph["arteria_source"] = "OpenStreetMap"
                graph.graph["arteria_mode"] = mode
                graph.graph["arteria_retrieved_at"] = timestamp
                graph.graph["arteria_area_key"] = key
                graphs[mode] = graph
                network_retrieved[mode] = timestamp
                if use_cache:
                    try:
                        temporary = graph_path.with_name(graph_path.stem + ".tmp.graphml")
                        ox.save_graphml(graph, filepath=temporary)
                        temporary.replace(graph_path)
                        graph_metadata.write_text(
                            json.dumps({
                                "mode": mode,
                                "area_key": key,
                                "retrieved_at": timestamp,
                                **_source_area_metadata(normalized),
                                "query": {"network_type": mode, "simplify": True, "retain_all": True, "truncate_by_edge": True},
                            }, indent=2, ensure_ascii=False, allow_nan=False),
                            encoding="utf-8",
                        )
                    except Exception as error:
                        warnings.append(f"Could not cache the acquired {mode} OSM network: {type(error).__name__}: {error}")

            if not graphs:
                details = "; ".join(network_failures.values()) or "no requested network produced a routable graph"
                raise OSMDataError(f"None of the requested OSM networks {requested_modes!r} is available: {details}")

            features = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
            cache_eligible = categories is None or bool(categories)
            if use_cache and not force_refresh and cache_eligible and features_path.exists():
                try:
                    features, feature_sidecar, feature_cache_verification = _load_verified_feature_cache(
                        features_path,
                        area=normalized,
                        area_key=key,
                        categories=categories,
                        query_tags=query_tags,
                    )
                    feature_retrieved = str(feature_sidecar.get("retrieved_at") or "unknown")
                    feature_raw_count = int(feature_sidecar.get("raw_feature_count", feature_sidecar.get("feature_count", len(features))))
                    rejected_geometry_count = int(feature_sidecar.get("rejected_geometry_count", 0))
                    feature_cache_hit = True
                    feature_cache_status = "hit"
                    feature_data_available = True
                except Exception as error:
                    feature_cache_status = "rejected"
                    if "source area" in str(error).casefold() or "geometry hash" in str(error).casefold() or "area key" in str(error).casefold():
                        feature_cache_verification = "unverified"
                    warnings.append(f"Ignoring unverified or incompatible OSM feature cache: {error}")
            elif use_cache and force_refresh and cache_eligible:
                feature_cache_status = "forced_refresh"

            if not feature_data_available and feature_query_requested:
                try:
                    if categories is not None:
                        settings.requests_timeout = FEATURE_REQUEST_TIMEOUT_SECONDS
                    raw_features = ox.features_from_polygon(normalized.polygon, tags=query_tags)
                    feature_raw_count = len(raw_features)
                    if feature_raw_count > MAX_OSM_FEATURE_COUNT:
                        raise ValueError(
                            f"OpenStreetMap returned {feature_raw_count} features, exceeding the {MAX_OSM_FEATURE_COUNT}-feature limit."
                        )
                    features, rejected_geometry_count = _clean_feature_frame(raw_features)
                    serialized = _serialized_feature_frame(features)
                    if len(serialized.encode("utf-8")) > MAX_OSM_FEATURE_JSON_BYTES:
                        raise ValueError(
                            f"OpenStreetMap feature output exceeds the {MAX_OSM_FEATURE_JSON_BYTES}-byte serialized limit."
                        )
                    feature_retrieved = _timestamp()
                    feature_data_available = True
                    feature_cache_verification = "verified_by_requested_geometry"
                    if feature_cache_status == "rejected":
                        feature_cache_status = "refreshed_after_rejection"
                    elif not use_cache:
                        feature_cache_status = "disabled"
                    else:
                        feature_cache_status = "miss"
                    if rejected_geometry_count:
                        warnings.append(
                            f"Dropped {rejected_geometry_count} invalid, unsupported, or out-of-range OpenStreetMap feature geometries."
                        )
                    if use_cache:
                        _cache_frame(features_path, features)
                        _network_metadata_path(features_path).write_text(
                            json.dumps({
                                "area_key": key,
                                "retrieved_at": feature_retrieved,
                                "feature_count": len(features),
                                "raw_feature_count": feature_raw_count,
                                "rejected_geometry_count": rejected_geometry_count,
                                "category_schema_version": FEATURE_CATEGORY_SCHEMA_VERSION if categories is not None else None,
                                "feature_categories": list(categories) if categories is not None else None,
                                "attribution": "© OpenStreetMap contributors",
                                "license": "ODbL-1.0",
                                **_source_area_metadata(normalized),
                                "query": {"tags": query_tags},
                            }, indent=2, ensure_ascii=False, allow_nan=False),
                            encoding="utf-8",
                        )
                except Exception as error:
                    feature_request_error = f"{type(error).__name__}: {error}"
                    feature_data_available = False
                    features = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
                    warnings.append(f"OpenStreetMap feature request failed: {feature_request_error}")
            elif not feature_data_available and categories is None and not include_features:
                warnings.append("OpenStreetMap feature layers were not requested for this graph-only study; their availability remains unknown.")
        finally:
            settings.cache_folder = previous["cache_folder"]
            settings.use_cache = previous["use_cache"]
            settings.requests_timeout = previous["requests_timeout"]
            settings.overpass_url = previous["overpass_url"]
            settings.http_user_agent = previous["http_user_agent"]

    layers = _layer_masks(features)
    if categories is not None:
        allowed_layers = set(categories) if feature_data_available else set()
        for name in layers:
            if name not in allowed_layers:
                layers[name] = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    loaded_categories = (
        tuple(FEATURE_CATEGORY_TAGS)
        if categories is None and feature_data_available
        else (categories or ()) if feature_data_available
        else ()
    )
    attempted_categories = tuple(FEATURE_CATEGORY_TAGS) if categories is None and feature_query_requested else (categories or ())
    category_availability: dict[str, dict[str, Any]] = {}
    for category, tag_filter in FEATURE_CATEGORY_TAGS.items():
        category_warnings = list(warnings) if category in attempted_categories or category in loaded_categories else []
        layer = layers.get(category)
        feature_count = int(len(layer)) if layer is not None else 0
        if category in loaded_categories:
            if feature_request_error and feature_count == 0:
                category_status = "request_failed"
            elif feature_raw_count and rejected_geometry_count == feature_raw_count and feature_count == 0:
                category_status = "request_failed"
            else:
                category_status = "available" if feature_count else "available_but_empty"
            count_value: int | None = feature_count
            area_verification = feature_cache_verification
        elif category in attempted_categories and feature_request_error:
            category_status = "request_failed"
            count_value = None
            area_verification = feature_cache_verification
        elif feature_cache_verification == "unverified" and not feature_query_requested:
            category_status = "source_unverified"
            count_value = None
            area_verification = "unverified"
        else:
            category_status = "not_requested"
            count_value = None
            area_verification = "not_checked"
        category_availability[category] = {
            "category_id": category,
            "status": category_status,
            "feature_count": count_value,
            "source_query": tag_filter,
            "source": "OpenStreetMap",
            "retrieved_at": feature_retrieved if category in loaded_categories else None,
            "cache_status": feature_cache_status if category in attempted_categories or category in loaded_categories else "not_requested",
            "area_verification": area_verification,
            "warnings": category_warnings,
        }

    availability: dict[str, dict[str, Any]] = {}
    for name, frame in layers.items():
        if name in category_availability:
            category_status = category_availability[name]["status"]
            status = "available" if category_status == "available" else "no_features_returned" if category_status == "available_but_empty" else "unknown"
        else:
            status = "available" if len(frame) else ("no_features_returned" if feature_data_available and categories is None else "unknown")
        availability[name] = {
            "status": status,
            "feature_count": int(len(frame)),
            "source_tag_filter": LAYER_TAGS[name],
            "coverage": "OpenStreetMap mapped/tagged features only; an empty result does not prove absence.",
        }
    for mode in requested_modes:
        if mode not in graphs:
            availability[f"{mode}_network"] = {
                "status": "request_failed",
                "reason": network_failures.get(mode, "Network request failed."),
            }
        else:
            availability[f"{mode}_network"] = {"status": "available", "node_count": int(graphs[mode].number_of_nodes()), "edge_count": int(graphs[mode].number_of_edges())}

    retrieved_values = [value for value in [*network_retrieved.values(), feature_retrieved] if value and value != "unknown"]
    metadata = {
        "source": "OpenStreetMap",
        "source_version": "live OSM snapshot",
        "requested_network_modes": list(requested_modes),
        "feature_query_requested": feature_query_requested,
        "feature_categories_requested": list(categories) if categories is not None else None,
        "feature_query_mode": "legacy_broad" if categories is None and include_features else "selected_categories" if categories else "disabled",
        "feature_category_schema_version": FEATURE_CATEGORY_SCHEMA_VERSION,
        "feature_category_availability": category_availability,
        "feature_query": {"tags": query_tags, "retrieved_at": feature_retrieved, "raw_feature_count": feature_raw_count, "rejected_geometry_count": rejected_geometry_count},
        "retrieved_at": max(retrieved_values) if retrieved_values else None,
        "extent_wgs84": normalized.extent,
        "area_key": key,
        **_source_area_metadata(normalized),
        "working_crs": normalized.working_crs,
        "network_retrieved_at": network_retrieved,
        "features_retrieved_at": feature_retrieved,
        "osm_tags": query_tags,
        "cache": {"enabled": bool(use_cache), "directory": "sim/.cache/osm" if cache_dir is None else "configured local cache", "application_snapshot_hit": bool(cache_hit_modes or feature_cache_hit), "cached_network_modes": cache_hit_modes, "features_cache_hit": feature_cache_hit, "features_status": feature_cache_status, "features_cache_key": feature_cache_key, "features_area_verification": feature_cache_verification},
        "limitations": [
            "OSM feature coverage and tags are incomplete and vary by area.",
            "An absent OSM feature is unknown, not evidence that infrastructure does not exist.",
            "Retrieved time describes this request; OSM does not expose a complete per-feature source timestamp in this query result.",
        ],
    }
    return OSMData(normalized, graphs, layers, availability, metadata, warnings)


def feature_collection(frame: gpd.GeoDataFrame) -> dict[str, Any]:
    """Return EPSG:4326 GeoJSON as a JSON-compatible FeatureCollection."""
    if frame.crs is None:
        raise ValueError("GeoDataFrame must have a declared CRS before GeoJSON export.")
    data = json.loads(frame.to_json(to_wgs84=True, drop_id=True, na="null", default=_json_default))
    data.setdefault("type", "FeatureCollection")
    return data


def _json_default(value: Any) -> Any:
    """Serialize provider date values and numpy scalars without losing tags."""
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return isoformat()
    item = getattr(value, "item", None)
    if callable(item):
        return item()
    return str(value)


def geojson_geometry(geometry: BaseGeometry, crs: str | CRS) -> dict[str, Any]:
    """Project a geometry to EPSG:4326 and serialize it as GeoJSON geometry."""
    frame = gpd.GeoSeries([geometry], crs=crs).to_crs("EPSG:4326")
    return mapping(frame.iloc[0])
