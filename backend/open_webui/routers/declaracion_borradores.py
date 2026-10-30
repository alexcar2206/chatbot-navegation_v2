"""API de borradores de la Declaración Responsable (almacenamiento principal en servidor).

El cliente genera los ids (UUID) para que reintentar un alta sin conexión no duplique,
y cada actualización envía la ``version`` que conoce: si otra escritura llegó antes se
responde 409 con el borrador actual para que el usuario elija.
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from open_webui.config import DECLARACION_BORRADORES_MAX, DECLARACION_BORRADORES_TTL_DIAS
from open_webui.models.declaracion_borradores import (
    ConflictoVersion,
    DeclaracionBorradores,
    DeclaracionBorradorForm,
    DeclaracionBorradorModel,
    DeclaracionBorradorResumen,
    IdEnUso,
)
from open_webui.navegacion.borradores import errores_borrador
from open_webui.navegacion.deps import require_feature

log = logging.getLogger(__name__)

router = APIRouter()

require_declaracion = require_feature(
    'declaracion.enable', 'features.declaracion', disabled_detail='Declaración deshabilitada'
)

E_MAX_BORRADORES = 'MAX_BORRADORES'
E_CONFLICTO_VERSION = 'CONFLICTO_VERSION'
E_ID_EN_USO = 'ID_EN_USO'

INTERVALO_PURGA_S = 3600
_ultima_purga = 0.0


class BorradorCrearBody(BaseModel):
    id: str = Field(..., min_length=8, max_length=64, pattern=r'^[A-Za-z0-9_-]+$')
    nombre: str
    paso: int
    datos: dict = Field(default_factory=dict)


class BorradorActualizarBody(BaseModel):
    nombre: str
    paso: int
    datos: dict = Field(default_factory=dict)
    version: int = Field(..., ge=1)


class BorradorCreadoResponse(DeclaracionBorradorModel):
    existente: bool = False


def _validar(nombre: str, paso: int, datos: dict) -> DeclaracionBorradorForm:
    errores = errores_borrador(nombre, paso, datos)
    if errores:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={'errores': errores})
    return DeclaracionBorradorForm(nombre=nombre.strip(), paso=paso, datos=datos)


async def purgar_borradores_caducados() -> int:
    global _ultima_purga
    _ultima_purga = time.monotonic()
    borrados = await DeclaracionBorradores.purgar_caducados(DECLARACION_BORRADORES_TTL_DIAS)
    if borrados:
        log.info('Purged %s expired declaration drafts (TTL %s days)', borrados, DECLARACION_BORRADORES_TTL_DIAS)
    return borrados


async def _purga_perezosa() -> None:
    if time.monotonic() - _ultima_purga < INTERVALO_PURGA_S:
        return
    try:
        await purgar_borradores_caducados()
    except Exception as e:
        log.warning('Declaration drafts purge failed: %s', e)


@router.get('/', response_model=list[DeclaracionBorradorResumen])
async def listar_borradores(user=Depends(require_declaracion)):
    await _purga_perezosa()
    return await DeclaracionBorradores.listar(user.id)


@router.get('/{id}', response_model=DeclaracionBorradorModel)
async def obtener_borrador(id: str, user=Depends(require_declaracion)):
    borrador = await DeclaracionBorradores.obtener(id, user.id)
    if borrador is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Borrador no encontrado')
    return borrador


@router.post('/', response_model=BorradorCreadoResponse)
async def crear_borrador(body: BorradorCrearBody, user=Depends(require_declaracion)):
    form = _validar(body.nombre, body.paso, body.datos)

    existente = await DeclaracionBorradores.obtener(body.id, user.id)
    if existente is not None:
        return BorradorCreadoResponse(**existente.model_dump(), existente=True)

    if await DeclaracionBorradores.contar(user.id) >= DECLARACION_BORRADORES_MAX:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                'codigo': E_MAX_BORRADORES,
                'maximo': DECLARACION_BORRADORES_MAX,
                'mensaje': f'Has alcanzado el máximo de {DECLARACION_BORRADORES_MAX} borradores.',
            },
        )

    try:
        borrador, ya_existia = await DeclaracionBorradores.crear(body.id, user.id, form)
    except IdEnUso:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={'codigo': E_ID_EN_USO, 'mensaje': 'Identificador de borrador no disponible.'},
        )
    return BorradorCreadoResponse(**borrador.model_dump(), existente=ya_existia)


@router.put('/{id}', response_model=DeclaracionBorradorModel)
async def actualizar_borrador(id: str, body: BorradorActualizarBody, user=Depends(require_declaracion)):
    form = _validar(body.nombre, body.paso, body.datos)
    try:
        borrador = await DeclaracionBorradores.actualizar(id, user.id, form, body.version)
    except ConflictoVersion as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'codigo': E_CONFLICTO_VERSION,
                'mensaje': 'El borrador se modificó desde otro sitio.',
                'actual': e.actual.model_dump(),
            },
        )
    if borrador is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Borrador no encontrado')
    return borrador


@router.delete('/{id}')
async def eliminar_borrador(id: str, user=Depends(require_declaracion)):
    # Idempotente: un borrado hecho sin conexión puede llegar cuando ya no existe.
    return {'eliminado': await DeclaracionBorradores.eliminar(id, user.id)}
