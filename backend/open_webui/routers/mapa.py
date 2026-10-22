"""API de consulta de zonas de navegación (Anexo 3 / mapa Miño-Sil).

Los handlers son ``def`` (no ``async``): geopandas es síncrono y FastAPI los
ejecuta en el threadpool para no bloquear el event loop.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from open_webui.navegacion.deps import require_feature
from open_webui.navegacion.geozona import (
    buscar_por_nombre,
    cache_disponible,
    consultar_punto,
    feature_por_nombre,
    geojson_highlight,
    listar_nombres_zonas,
    regenerar_geo_si_cambio,
    ruta_cache,
)
from open_webui.navegacion.runtime import clear_zonas_cache, get_geojson_display, get_zonas

log = logging.getLogger(__name__)

router = APIRouter()

MENSAJE_NO_DISPONIBLE = 'El mapa aún no está disponible. Espera a que termine el seed de docs_pack.'

require_mapa = require_feature('mapa.enable', 'features.mapa', disabled_detail='Mapa deshabilitado')
require_mapa_admin = require_feature('mapa.enable', 'features.mapa', admin=True, disabled_detail='Mapa deshabilitado')


def _ensure_geo_ready() -> None:
    """Solo comprueba: la regeneración ocurre en el lifespan o en ``POST /regenerar``."""
    if not cache_disponible():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=MENSAJE_NO_DISPONIBLE)


def _http_from_geo_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=MENSAJE_NO_DISPONIBLE)
    log.exception('Mapa query failed: %s', exc)
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail='No se pudo completar la consulta del mapa.',
    )


@router.get('/status')
def mapa_status(user=Depends(require_mapa)):
    respuesta = {'available': cache_disponible()}
    if user.role == 'admin':
        respuesta['cache_path'] = str(ruta_cache())
    return respuesta


@router.get('/nombres')
def mapa_nombres(user=Depends(require_mapa)):
    _ensure_geo_ready()
    try:
        nombres = listar_nombres_zonas(get_zonas())
    except Exception as e:
        raise _http_from_geo_error(e) from e
    return {'nombres': nombres}


@router.get('/geojson')
def mapa_geojson(user=Depends(require_mapa)):
    _ensure_geo_ready()
    try:
        return get_geojson_display()
    except Exception as e:
        raise _http_from_geo_error(e) from e


@router.get('/consulta')
def mapa_consulta(
    lat: float = Query(..., ge=-90, le=90, description='Latitud WGS84'),
    lon: float = Query(..., ge=-180, le=180, description='Longitud WGS84'),
    user=Depends(require_mapa),
):
    _ensure_geo_ready()
    try:
        return consultar_punto(lat, lon, gdf=get_zonas())
    except Exception as e:
        raise _http_from_geo_error(e) from e


@router.get('/buscar')
def mapa_buscar(
    q: str = Query(..., min_length=1, max_length=200, description='Nombre de embalse o zona'),
    user=Depends(require_mapa),
):
    _ensure_geo_ready()
    try:
        return buscar_por_nombre(q, gdf=get_zonas())
    except Exception as e:
        raise _http_from_geo_error(e) from e


@router.get('/highlight')
def mapa_highlight(
    nombre: Optional[str] = Query(None, max_length=200, description='Nombre de zona a resaltar'),
    user=Depends(require_mapa),
):
    _ensure_geo_ready()
    try:
        geojson = get_geojson_display()
        feature = feature_por_nombre(geojson, nombre)
        return geojson_highlight(feature)
    except Exception as e:
        raise _http_from_geo_error(e) from e


@router.post('/regenerar')
def mapa_regenerar(user=Depends(require_mapa_admin)):
    """Force geo_cache regen from docs_pack GDB (used by webui-seed after pack persist)."""
    result = regenerar_geo_si_cambio()
    clear_zonas_cache()
    available = cache_disponible()
    return {
        'ok': bool(result.get('ok')) and available,
        'available': available,
        'action': result.get('action'),
        'message': result.get('message'),
        'cache_path': str(ruta_cache()),
    }
