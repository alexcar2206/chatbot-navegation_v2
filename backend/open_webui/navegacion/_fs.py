"""Utilidades de sistema de ficheros para los artefactos generados (geo_cache, plantilla).

- ``escritura_atomica``: escribe en un temporal del mismo directorio y hace
  ``os.replace`` solo si todo termina bien, para que ningún lector vea un
  fichero a medio escribir ni quede un artefacto incompleto tras un error.
- ``lock_regeneracion``: lock entre procesos (varios workers de uvicorn) para
  que solo uno regenere a la vez.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock

from open_webui.env import DATA_DIR

LOCK_TIMEOUT_S = 600


@contextmanager
def escritura_atomica(destino: Path) -> Iterator[Path]:
    """Entrega una ruta temporal; al salir sin error la mueve a ``destino``."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f'.{destino.stem}.',
        suffix=f'.tmp{destino.suffix}',
        dir=destino.parent,
    )
    os.close(fd)
    tmp = Path(tmp_name)
    # Algunos writers (p.ej. el driver GeoJSON de GDAL) fallan si el fichero ya existe.
    tmp.unlink()
    try:
        yield tmp
        os.replace(tmp, destino)
    finally:
        tmp.unlink(missing_ok=True)


def escribir_json_atomico(destino: Path, datos: dict) -> None:
    with escritura_atomica(destino) as tmp:
        tmp.write_text(json.dumps(datos, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def lock_regeneracion(nombre: str) -> FileLock:
    directorio = Path(DATA_DIR) / 'locks'
    directorio.mkdir(parents=True, exist_ok=True)
    return FileLock(str(directorio / f'{nombre}.lock'), timeout=LOCK_TIMEOUT_S)
