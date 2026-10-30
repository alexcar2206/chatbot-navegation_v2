"""Validación de los borradores de la Declaración Responsable antes de guardarlos.

Un borrador puede estar incompleto o tener valores aún no válidos para generar el
documento; aquí solo se limita su forma (claves del esquema, tipos simples y tamaño).

Las claves que ya no existen en el esquema se descartan al guardar (evolución del
formulario) en lugar de rechazar el borrador entero.
"""

from __future__ import annotations

import json
from typing import Any

from open_webui.navegacion.formulario_dr import PASOS, TOTAL_PASOS

CLAVES_PERMITIDAS = frozenset(campo['clave'] for paso in PASOS for campo in paso['campos'])

MAX_BYTES_DATOS = 64 * 1024
MAX_LONGITUD_NOMBRE = 120
MAX_LONGITUD_VALOR = 2000
MAX_ELEMENTOS_LISTA = 200

E_NOMBRE_VACIO = 'NOMBRE_VACIO'
E_NOMBRE_LARGO = 'NOMBRE_LARGO'
E_PASO_RANGO = 'PASO_RANGO'
E_VALOR_INVALIDO = 'VALOR_INVALIDO'
E_DEMASIADO_GRANDE = 'DEMASIADO_GRANDE'


def _valor_simple_valido(valor: Any) -> bool:
    if valor is None or isinstance(valor, (bool, int, float)):
        return True
    if isinstance(valor, str):
        return len(valor) <= MAX_LONGITUD_VALOR
    return False


def _valor_valido(valor: Any) -> bool:
    if isinstance(valor, list):
        return len(valor) <= MAX_ELEMENTOS_LISTA and all(
            isinstance(v, str) and len(v) <= MAX_LONGITUD_VALOR for v in valor
        )
    return _valor_simple_valido(valor)


def sanitizar_datos(datos: dict) -> dict:
    """Devuelve solo las claves que existen en el esquema del formulario."""
    if not isinstance(datos, dict):
        return {}
    return {k: v for k, v in datos.items() if k in CLAVES_PERMITIDAS}


def errores_borrador(nombre: str, paso: int, datos: dict) -> list[dict[str, Any]]:
    """Lista de errores ``{codigo, mensaje, ...}``; vacía si el borrador se puede guardar.

    ``datos`` debe estar ya sanitizado (solo claves del esquema). Preferir
    ``preparar_borrador`` desde la API.
    """
    errores: list[dict[str, Any]] = []

    nombre_limpio = (nombre or '').strip()
    if not nombre_limpio:
        errores.append({'codigo': E_NOMBRE_VACIO, 'mensaje': 'El nombre del borrador es obligatorio.'})
    elif len(nombre_limpio) > MAX_LONGITUD_NOMBRE:
        errores.append(
            {
                'codigo': E_NOMBRE_LARGO,
                'mensaje': f'El nombre no puede superar {MAX_LONGITUD_NOMBRE} caracteres.',
            }
        )

    if not isinstance(paso, int) or isinstance(paso, bool) or not 1 <= paso <= TOTAL_PASOS:
        errores.append({'codigo': E_PASO_RANGO, 'mensaje': f'El paso debe estar entre 1 y {TOTAL_PASOS}.'})

    if not isinstance(datos, dict):
        errores.append({'codigo': E_VALOR_INVALIDO, 'mensaje': 'Los datos deben ser un objeto.', 'claves': []})
        return errores

    invalidas = sorted(k for k, v in datos.items() if not _valor_valido(v))
    if invalidas:
        errores.append(
            {
                'codigo': E_VALOR_INVALIDO,
                'mensaje': 'Algunos campos tienen un tipo de valor no admitido.',
                'claves': invalidas,
            }
        )

    if len(json.dumps(datos, ensure_ascii=False).encode('utf-8')) > MAX_BYTES_DATOS:
        errores.append(
            {
                'codigo': E_DEMASIADO_GRANDE,
                'mensaje': f'El borrador supera el tamaño máximo ({MAX_BYTES_DATOS // 1024} KB).',
            }
        )

    return errores


def preparar_borrador(
    nombre: str, paso: int, datos: Any
) -> tuple[list[dict[str, Any]], dict]:
    """Filtra claves desconocidas y valida. Devuelve ``(errores, datos_limpios)``."""
    if not isinstance(datos, dict):
        return errores_borrador(nombre, paso, datos), {}
    limpios = sanitizar_datos(datos)
    return errores_borrador(nombre, paso, limpios), limpios
