"""Cache en memoria del GeoDataFrame / GeoJSON de display para la API de mapa."""

from __future__ import annotations

import logging
import threading
from typing import Any

import geopandas as gpd

from open_webui.navegacion.geozona import cargar_zonas, geojson_para_mapa

log = logging.getLogger(__name__)

_lock = threading.RLock()
_zonas_gdf: gpd.GeoDataFrame | None = None
_geojson_display: dict[str, Any] | None = None


def clear_zonas_cache() -> None:
    global _zonas_gdf, _geojson_display
    with _lock:
        _zonas_gdf = None
        _geojson_display = None


def get_zonas() -> gpd.GeoDataFrame:
    global _zonas_gdf
    with _lock:
        if _zonas_gdf is None:
            _zonas_gdf = cargar_zonas()
            log.info('Loaded navigation zones cache (%s features)', len(_zonas_gdf))
        return _zonas_gdf


def get_geojson_display() -> dict[str, Any]:
    global _geojson_display
    with _lock:
        if _geojson_display is None:
            _geojson_display = geojson_para_mapa(get_zonas())
        return _geojson_display
