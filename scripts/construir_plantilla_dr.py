#!/usr/bin/env python3
"""CLI: construye la plantilla Jinja de la Declaración Responsable.

Uso (desde la raíz del repo, con el backend en PYTHONPATH):

    python scripts/construir_plantilla_dr.py

Requiere el DOCX editable en docs_pack (tras el seed) o DR_EDITABLE_DOCX_PATH.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / 'backend'
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from open_webui.navegacion.plantilla import (  # noqa: E402
    build_plantilla,
    ruta_editable,
    ruta_plantilla,
)


def main() -> int:
    editable = ruta_editable()
    plantilla = ruta_plantilla()
    print(f'Editable:  {editable}')
    print(f'Plantilla: {plantilla}')
    resultado = build_plantilla(editable=editable, plantilla=plantilla)
    print(f'Plantilla generada en: {resultado["plantilla"]}')
    print(f'Embalses taggeados ({len(resultado["embalses_taggeados"])}):')
    for nombre in resultado['embalses_taggeados']:
        print(f'  - {nombre}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
