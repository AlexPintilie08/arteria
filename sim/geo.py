"""Bounded, cached OpenStreetMap acquisition for ARTERIA."""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

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
    max_area_km2: float = DEFAULT_MAX_AREA_KM2,
    max_extent_km: float = DEFAULT_MAX_EXTENT_KM,
) -> OSMData:
    """Download OSM features and mode-specific graphs for a bounded area.

    OSMnx's standard Overpass rate limiting remains enabled. Both OSMnx HTTP
    responses and normalized GraphML/GeoJSON snapshots are cached under sim/.cache
    by default. Failed modes are reported when another requested graph succeeds;
    an all-mode failure raises OSMDataError. POI-query failures remain warnings.
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
    requested_modes = tuple(dict.fromkeys(mode_values))
    normalized = normalize_area(area, max_area_km2=max_area_km2, max_extent_km=max_extent_km)
    base = Path(cache_dir) if cache_dir else Path(__file__).resolve().parent / ".cache" / "osm"
    base.mkdir(parents=True, exist_ok=True)
    http_cache = base / "http"
    http_cache.mkdir(parents=True, exist_ok=True)
    key = _area_key(normalized)
    graphs: dict[str, Any] = {}
    warnings: list[str] = []
    network_retrieved: dict[str, str] = {}
    network_failures: dict[str, str] = {}
    cache_hit_modes: list[str] = []
    feature_retrieved: str | None = None
    feature_cache_hit = False
    features_path = base / f"{key}-features.geojson"

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
                            json.dumps({"mode": mode, "area_key": key, "retrieved_at": timestamp}, indent=2),
                            encoding="utf-8",
                        )
                    except Exception as error:
                        warnings.append(f"Could not cache the acquired {mode} OSM network: {type(error).__name__}: {error}")

            if not graphs:
                details = "; ".join(network_failures.values()) or "no requested network produced a routable graph"
                raise OSMDataError(f"None of the requested OSM networks {requested_modes!r} is available: {details}")

            if use_cache and not force_refresh and features_path.exists():
                try:
                    features = _load_cached_frame(features_path)
                    sidecar = _network_metadata_path(features_path)
                    feature_retrieved = json.loads(sidecar.read_text(encoding="utf-8"))["retrieved_at"] if sidecar.exists() else "unknown"
                    feature_cache_hit = True
                except Exception as error:
                    warnings.append(f"Ignoring unreadable OSM feature cache: {error}")
                    features = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
            else:
                features = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
            if feature_retrieved is None:
                try:
                    raw_features = ox.features_from_polygon(normalized.polygon, tags=FEATURE_TAGS)
                    features = _feature_frame(raw_features)
                    feature_retrieved = _timestamp()
                    if use_cache:
                        _cache_frame(features_path, features)
                        _network_metadata_path(features_path).write_text(
                            json.dumps({"area_key": key, "retrieved_at": feature_retrieved, "feature_count": len(features)}, indent=2),
                            encoding="utf-8",
                        )
                except Exception as error:
                    warnings.append(f"OpenStreetMap feature request failed: {type(error).__name__}: {error}")
        finally:
            settings.cache_folder = previous["cache_folder"]
            settings.use_cache = previous["use_cache"]
            settings.requests_timeout = previous["requests_timeout"]
            settings.overpass_url = previous["overpass_url"]
            settings.http_user_agent = previous["http_user_agent"]

    layers = _layer_masks(features)
    feature_status = "available" if feature_retrieved not in (None, "unknown") else "unknown"
    availability: dict[str, dict[str, Any]] = {}
    for name, frame in layers.items():
        status = "available" if len(frame) else ("no_features_returned" if feature_status == "available" else "unknown")
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
        "retrieved_at": max(retrieved_values) if retrieved_values else None,
        "extent_wgs84": normalized.extent,
        "area_key": key,
        "working_crs": normalized.working_crs,
        "network_retrieved_at": network_retrieved,
        "features_retrieved_at": feature_retrieved,
        "osm_tags": FEATURE_TAGS,
        "cache": {"enabled": bool(use_cache), "directory": "sim/.cache/osm" if cache_dir is None else "configured local cache", "application_snapshot_hit": bool(cache_hit_modes or feature_cache_hit), "cached_network_modes": cache_hit_modes, "features_cache_hit": feature_cache_hit},
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
