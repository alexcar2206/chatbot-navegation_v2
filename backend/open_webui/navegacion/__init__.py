"""Dominio Miño-Sil: zonas de navegación (mapa) y utilidades relacionadas."""

from open_webui.navegacion.geozona import (
    buscar_por_nombre,
    cache_disponible,
    cargar_zonas,
    consultar_punto,
    feature_por_nombre,
    geojson_highlight,
    geojson_para_mapa,
    listar_nombres_zonas,
    regenerar_geo_si_cambio,
    ruta_cache,
)
from open_webui.navegacion.runtime import clear_zonas_cache, get_geojson_display, get_zonas

__all__ = [
    'buscar_por_nombre',
    'cache_disponible',
    'cargar_zonas',
    'clear_zonas_cache',
    'consultar_punto',
    'feature_por_nombre',
    'geojson_highlight',
    'geojson_para_mapa',
    'get_geojson_display',
    'get_zonas',
    'listar_nombres_zonas',
    'regenerar_geo_si_cambio',
    'ruta_cache',
]
