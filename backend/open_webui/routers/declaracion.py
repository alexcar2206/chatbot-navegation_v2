"""API de Declaración Responsable de navegación (Miño-Sil MVP)."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from open_webui.models.config import Config
from open_webui.navegacion.formulario_dr import (
    LIMITACIONES_MVP,
    NUM_PASO_REVISION,
    TOTAL_PASOS,
    TOTAL_PASOS_DATOS,
    schema_pasos,
    titulo_paso,
    validar_global,
    validar_paso,
)
from open_webui.navegacion.generar_documento import generar_declaracion, nombre_archivo_descarga
from open_webui.navegacion.plantilla import (
    plantilla_disponible,
    regenerar_plantilla_si_cambio,
    ruta_editable,
    ruta_plantilla,
)
from open_webui.utils.auth import get_admin_user, get_verified_user

log = logging.getLogger(__name__)

router = APIRouter()

DOCX_MEDIA = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'


class DatosBody(BaseModel):
    datos: dict[str, Any] = Field(default_factory=dict)


class ValidarPasoBody(BaseModel):
    paso: int = Field(..., ge=1, le=TOTAL_PASOS)
    datos: dict[str, Any] = Field(default_factory=dict)


async def _require_declaracion_feature(user=Depends(get_verified_user)):
    enabled = await Config.get('declaracion.enable')
    if enabled is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='Declaración deshabilitada'
        )
    return user


async def _require_declaracion_admin(user=Depends(get_admin_user)):
    enabled = await Config.get('declaracion.enable')
    if enabled is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='Declaración deshabilitada'
        )
    return user


def _ensure_plantilla_ready() -> None:
    if plantilla_disponible():
        return
    result = regenerar_plantilla_si_cambio()
    if not result.get('ok') or not plantilla_disponible():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result.get('message')
            or (
                'Plantilla de declaración no disponible. Espera al seed de docs_pack '
                'o regenera la plantilla.'
            ),
        )


@router.get('/status')
async def declaracion_status(user=Depends(_require_declaracion_feature)):
    available = plantilla_disponible()
    if not available:
        try:
            _ensure_plantilla_ready()
            available = plantilla_disponible()
        except HTTPException:
            available = False
    return {
        'available': available,
        'plantilla_path': str(ruta_plantilla()),
        'editable_path': str(ruta_editable()),
        'limitaciones_mvp': LIMITACIONES_MVP,
        'total_pasos': TOTAL_PASOS,
        'total_pasos_datos': TOTAL_PASOS_DATOS,
        'paso_revision': NUM_PASO_REVISION,
    }


@router.get('/schema')
async def declaracion_schema(user=Depends(_require_declaracion_feature)):
    pasos = schema_pasos()
    return {
        'pasos': [
            {
                'indice': i + 1,
                'titulo': paso['titulo'],
                'campos': paso['campos'],
            }
            for i, paso in enumerate(pasos)
        ],
        'paso_revision': {
            'indice': NUM_PASO_REVISION,
            'titulo': titulo_paso(NUM_PASO_REVISION),
        },
        'limitaciones_mvp': LIMITACIONES_MVP,
        'total_pasos': TOTAL_PASOS,
    }


@router.post('/validar-paso')
async def declaracion_validar_paso(
    body: ValidarPasoBody,
    user=Depends(_require_declaracion_feature),
):
    if body.paso == NUM_PASO_REVISION:
        errores = validar_global(body.datos)
    elif body.paso > TOTAL_PASOS_DATOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'Paso fuera de rango: {body.paso}',
        )
    else:
        errores = validar_paso(body.paso, body.datos)
    return {'ok': not errores, 'errores': errores, 'paso': body.paso}


@router.post('/validar')
async def declaracion_validar(
    body: DatosBody,
    user=Depends(_require_declaracion_feature),
):
    errores = validar_global(body.datos)
    return {'ok': not errores, 'errores': errores}


@router.post('/generar')
async def declaracion_generar(
    body: DatosBody,
    user=Depends(_require_declaracion_feature),
):
    errores = validar_global(body.datos)
    if errores:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={'errores': errores},
        )

    _ensure_plantilla_ready()
    try:
        buffer = generar_declaracion(body.datos)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Plantilla de declaración no disponible',
        ) from exc
    except Exception as exc:
        log.exception('Error generando declaración: %s', exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='No se pudo generar el documento',
        ) from exc

    filename = nombre_archivo_descarga(body.datos)
    headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return StreamingResponse(buffer, media_type=DOCX_MEDIA, headers=headers)


@router.post('/regenerar')
async def declaracion_regenerar(user=Depends(_require_declaracion_admin)):
    """Force plantilla regen from docs_pack EDITABLE DOCX (used by webui-seed)."""
    result = regenerar_plantilla_si_cambio()
    available = plantilla_disponible()
    return {
        'ok': bool(result.get('ok')) and available,
        'available': available,
        'action': result.get('action'),
        'message': result.get('message'),
        'plantilla_path': str(ruta_plantilla()),
        'editable_path': str(ruta_editable()),
    }
