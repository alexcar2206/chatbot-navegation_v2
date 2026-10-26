"""Generación del DOCX de la Declaración Responsable (docxtpl)."""

from __future__ import annotations

import io
from pathlib import Path

from docxtpl import DocxTemplate

from open_webui.navegacion.formulario_dr import construir_contexto_plantilla, matricula_efectiva
from open_webui.navegacion.plantilla import plantilla_disponible, ruta_plantilla


def generar_declaracion(datos: dict, plantilla: Path | None = None) -> io.BytesIO:
    """Rellena la plantilla y devuelve un buffer DOCX en memoria."""
    path = Path(plantilla) if plantilla is not None else ruta_plantilla()
    if not plantilla_disponible(path):
        raise FileNotFoundError(
            f"No se encontró la plantilla en '{path}'. "
            'Arranca el servicio con docs_pack disponible o ejecuta '
            'scripts/construir_plantilla_dr.py.'
        )

    contexto = construir_contexto_plantilla(datos)
    documento = DocxTemplate(str(path))
    # autoescape: los datos del usuario (p.ej. "Pérez & Hijos") se insertan como
    # texto; sin escapar, '&' o '<' romperían el XML del documento.
    documento.render(contexto, autoescape=True)

    buffer = io.BytesIO()
    documento.save(buffer)
    buffer.seek(0)
    return buffer


def nombre_archivo_descarga(datos: dict, extension: str = 'docx') -> str:
    matricula = matricula_efectiva(datos) or 'declaracion'
    # Solo ASCII: el nombre viaja en una cabecera HTTP (latin-1).
    matricula_segura = ''.join(c if (c.isascii() and c.isalnum()) or c in '-_' else '_' for c in matricula)
    ext = extension.lstrip('.').lower() or 'docx'
    return f'Declaracion_responsable_{matricula_segura}.{ext}'
