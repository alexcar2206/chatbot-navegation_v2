"""API de consulta de zonas de navegación (Anexo 3 / mapa Miño-Sil)."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from open_webui.models.config import Config
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
from open_webui.utils.auth import get_admin_user, get_verified_user

log = logging.getLogger(__name__)

router = APIRouter()


async def _require_mapa_feature(user=Depends(get_verified_user)):
    enabled = await Config.get('mapa.enable')
    if enabled is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Mapa deshabilitado')
    return user


async def _require_mapa_admin(user=Depends(get_admin_user)):
    enabled = await Config.get('mapa.enable')
    if enabled is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Mapa deshabilitado')
    return user


def _ensure_geo_ready() -> None:
    """If seed finished after startup, generate cache on first map request."""
    if cache_disponible():
        return
    result = regenerar_geo_si_cambio()
    clear_zonas_cache()
    if not result.get('ok') or not cache_disponible():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result.get('message')
            or 'Cache geográfico no disponible. Espera al seed de docs_pack o regenera geo_cache/.',
        )


def _http_from_geo_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    log.exception('Mapa query failed: %s', exc)
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f'No se pudo completar la consulta del mapa: {exc}',
    )


@router.get('/status')
async def mapa_status(user=Depends(_require_mapa_feature)):
    available = cache_disponible()
    if not available:
        try:
            _ensure_geo_ready()
            available = cache_disponible()
        except HTTPException:
            available = False
    return {
        'available': available,
        'cache_path': str(ruta_cache()),
    }


@router.get('/nombres')
async def mapa_nombres(user=Depends(_require_mapa_feature)):
    _ensure_geo_ready()
    try:
        nombres = listar_nombres_zonas(get_zonas())
    except Exception as e:
        raise _http_from_geo_error(e) from e
    return {'nombres': nombres}


@router.get('/geojson')
async def mapa_geojson(user=Depends(_require_mapa_feature)):
    _ensure_geo_ready()
    try:
        return get_geojson_display()
    except Exception as e:
        raise _http_from_geo_error(e) from e


@router.get('/consulta')
async def mapa_consulta(
    lat: float = Query(..., description='Latitud WGS84'),
    lon: float = Query(..., description='Longitud WGS84'),
    user=Depends(_require_mapa_feature),
):
    _ensure_geo_ready()
    try:
        return consultar_punto(lat, lon, gdf=get_zonas())
    except Exception as e:
        raise _http_from_geo_error(e) from e


@router.get('/buscar')
async def mapa_buscar(
    q: str = Query(..., min_length=1, description='Nombre de embalse o zona'),
    user=Depends(_require_mapa_feature),
):
    _ensure_geo_ready()
    try:
        return buscar_por_nombre(q, gdf=get_zonas())
    except Exception as e:
        raise _http_from_geo_error(e) from e


@router.get('/highlight')
async def mapa_highlight(
    nombre: Optional[str] = Query(None, description='Nombre de zona a resaltar'),
    user=Depends(_require_mapa_feature),
):
    _ensure_geo_ready()
    try:
        geojson = get_geojson_display()
        feature = feature_por_nombre(geojson, nombre)
        return geojson_highlight(feature)
    except Exception as e:
        raise _http_from_geo_error(e) from e


@router.post('/regenerar')
async def mapa_regenerar(user=Depends(_require_mapa_admin)):
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
