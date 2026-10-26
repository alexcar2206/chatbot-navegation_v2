"""Cache en memoria del GeoDataFrame / GeoJSON de display para la API de mapa.

La cache se invalida sola cuando cambia el fichero GeoJSON en disco (mtime y
tamaño), de modo que todos los workers ven la regeneración hecha por cualquiera
de ellos sin necesidad de coordinarse.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

import geopandas as gpd

from open_webui.navegacion.geozona import cargar_zonas, geojson_para_mapa, preparar_zonas, ruta_cache

log = logging.getLogger(__name__)

_lock = threading.RLock()
_firma: tuple[int, int] | None = None
_zonas_gdf: gpd.GeoDataFrame | None = None
_geojson_display: dict[str, Any] | None = None


def _firma_cache() -> tuple[int, int] | None:
    try:
        st = ruta_cache().stat()
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size)


def clear_zonas_cache() -> None:
    global _firma, _zonas_gdf, _geojson_display
    with _lock:
        _firma = None
        _zonas_gdf = None
        _geojson_display = None


def _invalidar_si_cambio() -> None:
    firma = _firma_cache()
    if firma != _firma:
        clear_zonas_cache()


def get_zonas() -> gpd.GeoDataFrame:
    global _firma, _zonas_gdf
    with _lock:
        _invalidar_si_cambio()
        if _zonas_gdf is None:
            firma = _firma_cache()
            _zonas_gdf = preparar_zonas(cargar_zonas())
            _firma = firma
            log.info('Loaded navigation zones cache (%s features)', len(_zonas_gdf))
        return _zonas_gdf


def get_geojson_display() -> dict[str, Any]:
    global _geojson_display
    with _lock:
        zonas = get_zonas()
        if _geojson_display is None:
            _geojson_display = geojson_para_mapa(zonas)
        return _geojson_display
