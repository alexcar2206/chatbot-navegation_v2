"""API de Declaración Responsable de navegación (Miño-Sil MVP).

Los handlers son ``def`` (no ``async``): docxtpl/python-docx son síncronos y
FastAPI los ejecuta en el threadpool para no bloquear el event loop.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from open_webui.config import DECLARACION_BORRADORES_TTL_DIAS
from open_webui.navegacion.deps import require_feature
from open_webui.navegacion.formulario_dr import (
    LIMITACIONES_MVP,
    NUM_PASO_REVISION,
    TOTAL_PASOS,
    TOTAL_PASOS_DATOS,
    matricula_efectiva,
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

log = logging.getLogger(__name__)

router = APIRouter()

DOCX_MEDIA = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
MENSAJE_NO_DISPONIBLE = (
    'La plantilla de declaración aún no está disponible. Espera a que termine el seed de docs_pack.'
)

require_declaracion = require_feature(
    'declaracion.enable', 'features.declaracion', disabled_detail='Declaración deshabilitada'
)
require_declaracion_admin = require_feature(
    'declaracion.enable', 'features.declaracion', admin=True, disabled_detail='Declaración deshabilitada'
)


class DatosBody(BaseModel):
    datos: dict[str, Any] = Field(default_factory=dict)


class ValidarPasoBody(BaseModel):
    paso: int = Field(..., ge=1, le=TOTAL_PASOS)
    datos: dict[str, Any] = Field(default_factory=dict)


def _ensure_plantilla_ready() -> None:
    """Solo comprueba: la regeneración ocurre en el lifespan o en ``POST /regenerar``."""
    if not plantilla_disponible():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=MENSAJE_NO_DISPONIBLE)


@router.get('/status')
def declaracion_status(user=Depends(require_declaracion)):
    respuesta = {
        'available': plantilla_disponible(),
        'limitaciones_mvp': LIMITACIONES_MVP,
        'total_pasos': TOTAL_PASOS,
        'total_pasos_datos': TOTAL_PASOS_DATOS,
        'paso_revision': NUM_PASO_REVISION,
        'borradores_ttl_dias': DECLARACION_BORRADORES_TTL_DIAS,
    }
    if user.role == 'admin':
        respuesta['plantilla_path'] = str(ruta_plantilla())
        respuesta['editable_path'] = str(ruta_editable())
    return respuesta


@router.get('/schema')
def declaracion_schema(user=Depends(require_declaracion)):
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
def declaracion_validar_paso(
    body: ValidarPasoBody,
    user=Depends(require_declaracion),
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
def declaracion_validar(
    body: DatosBody,
    user=Depends(require_declaracion),
):
    errores = validar_global(body.datos)
    # La matrícula que se imprimirá: el frontend la muestra en la revisión como valor autoritativo.
    return {'ok': not errores, 'errores': errores, 'matricula': matricula_efectiva(body.datos)}


@router.post('/generar')
def declaracion_generar(
    body: DatosBody,
    user=Depends(require_declaracion),
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
    headers = {'Content-Disposition': f"attachment; filename=\"{filename}\"; filename*=UTF-8''{quote(filename)}"}
    return StreamingResponse(buffer, media_type=DOCX_MEDIA, headers=headers)


@router.post('/regenerar')
def declaracion_regenerar(user=Depends(require_declaracion_admin)):
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
