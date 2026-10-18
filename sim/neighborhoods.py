"""Import and validate sourced neighborhood place geometry."""

from __future__ import annotations

import copy
import json
import math
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping

import geopandas as gpd
from pyproj import CRS
from shapely.geometry import Point, mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity

from .geo import AreaValidationError, StudyArea, normalize_area


DEFAULT_NEIGHBORHOOD_CATALOG = Path(__file__).with_name("iasi-neighborhoods.geojson")
SUPPORTED_NEIGHBORHOOD_GEOMETRIES = {"Point", "Polygon", "MultiPolygon"}


class NeighborhoodCatalogError(ValueError):
    """Raised when a neighborhood catalog is malformed or has ambiguous IDs."""


def _plain_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise NeighborhoodCatalogError(f"Neighborhood {field} must be a non-empty string.")
    return value.strip()


def _finite_wgs84(geometry: BaseGeometry) -> bool:
    try:
        coordinates = geometry.coords if isinstance(geometry, Point) else None
        if coordinates is None:
            from shapely import get_coordinates

            coordinates = get_coordinates(geometry)
        for coordinate in coordinates:
            if len(coordinate) < 2:
                return False
            longitude, latitude = float(coordinate[0]), float(coordinate[1])
            if not math.isfinite(longitude) or not math.isfinite(latitude):
                return False
            if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
                return False
        return True
    except (TypeError, ValueError, OverflowError):
        return False


def _source_payload(source: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if source is None:
        source = DEFAULT_NEIGHBORHOOD_CATALOG
    if isinstance(source, (str, Path)):
        path = Path(source)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise NeighborhoodCatalogError(f"Could not read neighborhood catalog {path}: {error}") from error
    else:
        payload = source
    if isinstance(payload, list):
        metadata: dict[str, Any] = {}
        features = payload
    elif isinstance(payload, Mapping) and payload.get("type") == "FeatureCollection":
        metadata = dict(payload.get("metadata") or {})
        features = payload.get("features")
        declared_crs = metadata.get("coordinate_reference_system")
        if declared_crs is None and payload.get("crs"):
            crs_value = payload["crs"]
            declared_crs = crs_value.get("properties", {}).get("name") if isinstance(crs_value, Mapping) else crs_value
        if declared_crs is not None:
            try:
                if CRS.from_user_input(declared_crs).to_epsg() != 4326:
                    raise NeighborhoodCatalogError("Neighborhood GeoJSON must use EPSG:4326 coordinates.")
            except NeighborhoodCatalogError:
                raise
            except Exception as error:
                raise NeighborhoodCatalogError(f"Neighborhood catalog declares an invalid CRS: {declared_crs!r}.") from error
    else:
        raise NeighborhoodCatalogError("Neighborhood catalog must be a GeoJSON FeatureCollection or a list of features.")
    if not isinstance(features, list):
        raise NeighborhoodCatalogError("Neighborhood catalog features must be a list.")
    return metadata, features


def _normalize_feature(feature: Any, catalog_metadata: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(feature, Mapping) or feature.get("type") != "Feature":
        raise NeighborhoodCatalogError("Each neighborhood catalog item must be a GeoJSON Feature.")
    properties = feature.get("properties")
    if not isinstance(properties, Mapping):
        raise NeighborhoodCatalogError("Neighborhood feature properties must be an object.")
    identifier = properties.get("neighborhood_id") or properties.get("place_point_id") or feature.get("id")
    identifier = _plain_text(identifier, "identifier")
    name = _plain_text(properties.get("name"), "name")
    aliases = properties.get("alternative_names", [])
    if not isinstance(aliases, list) or any(not isinstance(alias, str) for alias in aliases):
        raise NeighborhoodCatalogError(f"Neighborhood {identifier!r} alternative_names must be a list of strings.")
    aliases = list(dict.fromkeys(alias.strip() for alias in aliases if alias.strip() and alias.strip() != name))
    geometry_data = feature.get("geometry")
    if not isinstance(geometry_data, Mapping):
        raise NeighborhoodCatalogError(f"Neighborhood {identifier!r} is missing GeoJSON geometry.")
    try:
        geometry = shape(geometry_data)
    except Exception as error:
        raise NeighborhoodCatalogError(f"Neighborhood {identifier!r} has malformed geometry: {error}") from error
    if geometry.geom_type not in SUPPORTED_NEIGHBORHOOD_GEOMETRIES:
        raise NeighborhoodCatalogError(f"Neighborhood {identifier!r} geometry must be Point, Polygon, or MultiPolygon.")
    if geometry.is_empty or not _finite_wgs84(geometry):
        raise NeighborhoodCatalogError(f"Neighborhood {identifier!r} geometry must have finite EPSG:4326 coordinates.")
    if not geometry.is_valid:
        raise NeighborhoodCatalogError(f"Neighborhood {identifier!r} has invalid geometry: {explain_validity(geometry)}")
    if geometry.geom_type in {"Polygon", "MultiPolygon"} and geometry.area <= 0:
        raise NeighborhoodCatalogError(f"Neighborhood {identifier!r} polygon has no area.")
    boundary_status = str(properties.get("boundary_status") or ("point_only" if geometry.geom_type == "Point" else "source_mapped"))
    if geometry.geom_type == "Point" and boundary_status != "point_only":
        raise NeighborhoodCatalogError(f"Neighborhood {identifier!r} is a point and must use boundary_status='point_only'.")
    if geometry.geom_type != "Point" and boundary_status == "point_only":
        raise NeighborhoodCatalogError(f"Neighborhood {identifier!r} is a polygon and cannot use boundary_status='point_only'.")
    source = _plain_text(properties.get("source") or catalog_metadata.get("source"), "source")
    source_object_id = _plain_text(properties.get("source_object_id") or identifier, "source_object_id")
    retrieved_at = properties.get("retrieved_at") or properties.get("updated_at") or catalog_metadata.get("retrieved_at")
    uncertainty = properties.get("uncertainty_notes") or properties.get("uncertainty")
    provenance = properties.get("provenance")
    if not isinstance(provenance, Mapping):
        provenance = {
            "source": source,
            "source_object_id": source_object_id,
            "retrieved_at": retrieved_at,
            "license": properties.get("license") or catalog_metadata.get("license"),
        }
    extras = {key: copy.deepcopy(value) for key, value in properties.items() if key not in {
        "neighborhood_id", "place_point_id", "name", "alternative_names", "source", "source_object_id",
        "boundary_status", "review_status", "retrieved_at", "updated_at", "uncertainty_notes", "uncertainty", "provenance",
    }}
    return {
        "id": identifier,
        "name": name,
        "alternative_names": aliases,
        "geometry": mapping(geometry),
        "geometry_type": geometry.geom_type,
        "source": source,
        "source_object_id": source_object_id,
        "boundary_status": boundary_status,
        "review_status": str(properties.get("review_status") or "unreviewed"),
        "provenance": copy.deepcopy(dict(provenance)),
        "retrieved_at": retrieved_at,
        "updated_at": properties.get("updated_at") or retrieved_at,
        "uncertainty_notes": str(uncertainty or "Source coverage and boundary authority are not established."),
        "properties": extras,
    }


def load_neighborhood_catalog(source: Any = None) -> list[dict[str, Any]]:
    """Load a GeoJSON neighborhood catalog as normalized JSON-compatible records.

    With no ``source``, the partial OSM-derived Iași catalog shipped with SIM is
    loaded. A source may be a path, a FeatureCollection, or a list of features.
    """
    metadata, features = _source_payload(source)
    records = [_normalize_feature(feature, metadata) for feature in features]
    identifiers = [record["id"] for record in records]
    duplicates = sorted({identifier for identifier in identifiers if identifiers.count(identifier) > 1})
    if duplicates:
        raise NeighborhoodCatalogError(f"Neighborhood identifiers must be unique; duplicates: {duplicates!r}.")
    records.sort(key=lambda record: (record["name"].casefold(), record["id"]))
    return records


def get_neighborhoods(catalog: Any = None) -> list[dict[str, Any]]:
    """Return all neighborhood/place records, including point-only records."""
    return copy.deepcopy(load_neighborhood_catalog(catalog))


def get_neighborhood(identifier: str, catalog: Any = None) -> dict[str, Any] | None:
    """Return one record by stable catalog identifier, or ``None`` if absent."""
    for record in load_neighborhood_catalog(catalog):
        if record["id"] == identifier:
            return copy.deepcopy(record)
    return None


def _search_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold().strip())
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def search_neighborhoods(query: str, catalog: Any = None, *, limit: int = 20) -> list[dict[str, Any]]:
    """Search stable IDs, names, and alternative names with accent-insensitive matching."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Neighborhood search query must be a non-empty string.")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1 or limit > 500:
        raise ValueError("Neighborhood search limit must be an integer from 1 through 500.")
    needle = _search_key(query)
    matches = []
    for record in load_neighborhood_catalog(catalog):
        searchable = [record["id"], record["name"], *record["alternative_names"]]
        if any(needle in _search_key(value) for value in searchable):
            matches.append(record)
    return copy.deepcopy(matches[:limit])


def neighborhoods_geojson(identifier: str | None = None, catalog: Any = None) -> dict[str, Any]:
    """Serialize records as a stable EPSG:4326 GeoJSON FeatureCollection."""
    metadata, _ = _source_payload(catalog)
    records = load_neighborhood_catalog(catalog)
    if identifier is not None:
        records = [record for record in records if record["id"] == identifier]
    if identifier is not None and not records:
        raise KeyError(f"Unknown neighborhood identifier: {identifier!r}.")
    features = []
    for record in records:
        props = {
            "neighborhood_id": record["id"],
            "name": record["name"],
            "alternative_names": record["alternative_names"],
            "source": record["source"],
            "source_object_id": record["source_object_id"],
            "boundary_status": record["boundary_status"],
            "review_status": record["review_status"],
            "provenance": record["provenance"],
            "retrieved_at": record["retrieved_at"],
            "updated_at": record["updated_at"],
            "uncertainty_notes": record["uncertainty_notes"],
            **record["properties"],
        }
        features.append({"type": "Feature", "id": record["id"], "geometry": record["geometry"], "properties": props})
    return {"type": "FeatureCollection", "metadata": metadata, "features": features}


def _record_geometry(neighborhood: str | Mapping[str, Any], catalog: Any = None) -> tuple[str, Mapping[str, Any], dict[str, Any]]:
    if isinstance(neighborhood, str):
        record = get_neighborhood(neighborhood, catalog)
        if record is None:
            raise KeyError(f"Unknown neighborhood identifier: {neighborhood!r}.")
        return record["id"], record["geometry"], record
    if not isinstance(neighborhood, Mapping):
        raise TypeError("A neighborhood identifier or record mapping is required.")
    if neighborhood.get("type") == "Feature":
        properties = neighborhood.get("properties") or {}
        identifier = properties.get("neighborhood_id") or properties.get("place_point_id") or neighborhood.get("id") or "selected-neighborhood"
        geometry_data = neighborhood.get("geometry")
    else:
        identifier = neighborhood.get("id") or neighborhood.get("neighborhood_id") or neighborhood.get("place_point_id") or "selected-neighborhood"
        geometry_data = neighborhood.get("geometry")
    if not isinstance(geometry_data, Mapping):
        raise ValueError("Selected neighborhood record must include GeoJSON geometry.")
    try:
        geometry = shape(geometry_data)
    except Exception as error:
        raise ValueError(f"Selected neighborhood geometry is malformed: {error}") from error
    normalized = dict(neighborhood)
    normalized.setdefault("boundary_status", "point_only" if geometry.geom_type == "Point" else "source_mapped")
    normalized.setdefault("source", "user_imported")
    normalized.setdefault("source_object_id", str(identifier))
    return str(identifier), mapping(geometry), normalized


def validate_neighborhood_boundary(
    neighborhood: str | Mapping[str, Any],
    catalog: Any = None,
    *,
    max_area_km2: float = 5.0,
    max_extent_km: float = 5.0,
) -> dict[str, Any]:
    """Validate a selected polygon without modifying it or inferring point areas.

    An area over the configured limits is reported as requiring controlled
    analysis. Passing larger explicit limits performs that controlled check.
    """
    identifier, geometry_data, record = _record_geometry(neighborhood, catalog)
    try:
        geometry = shape(geometry_data)
    except Exception as error:
        return {"id": identifier, "status": "invalid", "analysis_eligible": False, "reason": f"Malformed GeoJSON geometry: {error}", "area_km2": None}
    if geometry.geom_type == "Point" or record.get("boundary_status") == "point_only":
        return {
            "id": identifier,
            "status": "point_only",
            "analysis_eligible": False,
            "reason": "This record contains a named point only; no neighborhood boundary is inferred.",
            "area_km2": None,
            "source_object_id": record.get("source_object_id"),
        }
    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        return {"id": identifier, "status": "invalid", "analysis_eligible": False, "reason": "Boundary must be a Polygon or MultiPolygon.", "area_km2": None}
    declared_crs = record.get("crs") or record.get("coordinate_reference_system") or "EPSG:4326"
    try:
        if CRS.from_user_input(declared_crs).to_epsg() != 4326:
            raise AreaValidationError("Selected GeoJSON coordinates must use EPSG:4326.")
    except AreaValidationError as error:
        return {"id": identifier, "status": "invalid", "analysis_eligible": False, "reason": str(error), "area_km2": None}
    except Exception as error:
        return {"id": identifier, "status": "invalid", "analysis_eligible": False, "reason": f"Invalid declared CRS: {error}", "area_km2": None}
    if geometry.is_empty or not _finite_wgs84(geometry) or not geometry.is_valid:
        reason = explain_validity(geometry) if not geometry.is_empty else "Boundary geometry is empty."
        return {"id": identifier, "status": "invalid", "analysis_eligible": False, "reason": reason, "area_km2": None}
    try:
        normalized = normalize_area(
            {"city_id": str(record.get("city_id") or "iasi-ro"), "area_id": identifier, "boundary": geometry_data,
             "boundary_source": f"catalog:{record.get('source', 'unknown')}:{record.get('source_object_id', identifier)}", "crs": "EPSG:4326"},
            max_area_km2=max_area_km2,
            max_extent_km=max_extent_km,
        )
    except (AreaValidationError, ValueError) as error:
        return {
            "id": identifier,
            "status": "requires_controlled_analysis" if "no larger" in str(error) or "extent must not exceed" in str(error) else "invalid",
            "analysis_eligible": False,
            "reason": str(error),
            "area_km2": _area_km2(geometry),
            "configured_limits": {"max_area_km2": max_area_km2, "max_extent_km": max_extent_km},
        }
    area_km2 = _area_km2(geometry)
    return {
        "id": identifier,
        "status": "valid",
        "analysis_eligible": True,
        "reason": None,
        "area_km2": area_km2,
        "working_crs": normalized.working_crs,
        "boundary_source": normalized.boundary_source,
        "source_object_id": record.get("source_object_id"),
    }


def _area_km2(geometry: BaseGeometry) -> float | None:
    try:
        series = gpd.GeoSeries([geometry], crs="EPSG:4326")
        metric_crs = series.estimate_utm_crs()
        if metric_crs is None:
            return None
        return float(series.to_crs(metric_crs).area.iloc[0] / 1_000_000)
    except Exception:
        return None


def neighborhood_area_input(
    neighborhood: str | Mapping[str, Any],
    catalog: Any = None,
    *,
    max_area_km2: float = 5.0,
    max_extent_km: float = 5.0,
) -> dict[str, Any]:
    """Return a validated ``normalize_area`` input or raise on limitations."""
    identifier, geometry_data, record = _record_geometry(neighborhood, catalog)
    validation = validate_neighborhood_boundary(
        neighborhood, catalog, max_area_km2=max_area_km2, max_extent_km=max_extent_km
    )
    if not validation["analysis_eligible"]:
        raise AreaValidationError(f"Neighborhood {identifier!r} is not eligible for standard area analysis: {validation['reason']}")
    return {
        "city_id": str(record.get("city_id") or "iasi-ro"),
        "area_id": identifier,
        "boundary": copy.deepcopy(geometry_data),
        "crs": "EPSG:4326",
        "boundary_source": f"catalog:{record.get('source', 'unknown')}:{record.get('source_object_id', identifier)}",
    }
