"""Consultas espaciales sobre las zonas de navegación del Anexo 3 (Miño-Sil).

Carga un GeoJSON cacheado (generado desde el File Geodatabase del pack de
documentación) y responde consultas por punto/nombre, incluyendo coincidencia
con la lista MVP de embalses.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point

from open_webui.env import DATA_DIR
from open_webui.navegacion._fs import escribir_json_atomico, escritura_atomica, lock_regeneracion
from open_webui.navegacion.constants import EMBALSES_OPCION_A

log = logging.getLogger(__name__)

DEFAULT_DOCS_PACK = DATA_DIR / 'docs_pack'
DEFAULT_GDB_RELATIVE = (
    Path('Formularios, Instrucciones de cumplimentación y anexos')
    / 'GEODATA ZONAS DE NAVEGACION ANEXO 3.gdb'
    / 'EMBALSES_NAVEGABILIDAD.gdb'
)
DEFAULT_CACHE_PATH = DATA_DIR / 'geo_cache' / 'zonas_navegacion.geojson'

METADATA_VERSION = 2
SIMPLIFY_TOLERANCE_M = 1.0
CRS_METRICO = 25829

COLUMNAS_NOMBRE = (
    'NOMBRE',
    'EMBALSE',
    'ZONA',
    'NOM_EMB',
    'NOM_ZONA',
    'NAME',
    'nombre',
    'embalse',
    'zona',
    'NomEmbalse',
    'NomZona',
)


def ruta_docs_pack() -> Path:
    return Path(os.getenv('GEO_DOCS_PACK_PATH', str(DEFAULT_DOCS_PACK)))


def default_gdb_path() -> Path:
    return ruta_docs_pack() / DEFAULT_GDB_RELATIVE


def _parece_file_geodatabase(ruta: Path) -> bool:
    if not ruta.is_dir():
        return False
    try:
        return any(p.suffix.lower() == '.gdbtable' for p in ruta.iterdir())
    except OSError:
        return False


def resolver_ruta_gdb(ruta: Path | None = None) -> Path:
    """Resuelve la ruta al `.gdb` real, incluso si viene una carpeta contenedora."""
    candidata = Path(ruta) if ruta is not None else Path(os.getenv('GEO_GDB_PATH', str(default_gdb_path())))
    if _parece_file_geodatabase(candidata):
        return candidata

    if candidata.is_dir():
        anidados = sorted(p for p in candidata.iterdir() if p.is_dir() and p.name.lower().endswith('.gdb'))
        for anidado in anidados:
            if _parece_file_geodatabase(anidado):
                return anidado
        if len(anidados) == 1:
            return anidados[0]

    return candidata


def ruta_gdb() -> Path:
    return resolver_ruta_gdb()


def ruta_cache() -> Path:
    return Path(os.getenv('GEO_CACHE_PATH', str(DEFAULT_CACHE_PATH)))


def ruta_metadata(cache_path: Path | None = None) -> Path:
    return (cache_path or ruta_cache()).parent / 'metadata.json'


def iterar_archivos_gdb(gdb_dir: Path) -> list[Path]:
    base = Path(gdb_dir)
    if not base.is_dir():
        return []

    archivos: list[Path] = []
    for root, _, files in os.walk(base):
        for nombre in files:
            ruta = Path(root) / nombre
            try:
                if ruta.is_file():
                    archivos.append(ruta)
            except OSError:
                continue
    return sorted(archivos)


def _sha256_archivo(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open('rb') as fh:
        for bloque in iter(lambda: fh.read(65536), b''):
            digest.update(bloque)
    return digest.hexdigest()


def _capa_para_huella(gdb: Path, layer: str | None = None) -> str:
    geo_capa_env = os.getenv('GEO_CAPA_ZONAS', '').strip()
    if layer:
        return layer
    if geo_capa_env:
        return geo_capa_env
    if _parece_file_geodatabase(gdb):
        return detectar_capa_zonas(gdb)
    return ''


def huella_gdb(
    gdb_path: Path | None = None,
    *,
    layer: str | None = None,
    previa: dict | None = None,
) -> dict:
    """Huella del .gdb. Si ``previa`` trae el mismo size/mtime de un fichero,
    se reutiliza su sha256 en vez de volver a leerlo entero."""
    gdb = resolver_ruta_gdb(gdb_path) if gdb_path is not None else ruta_gdb()
    geo_capa_env = os.getenv('GEO_CAPA_ZONAS', '').strip()
    capa = _capa_para_huella(gdb, layer=layer)
    files_previos = (previa or {}).get('files') or {}
    files: dict[str, dict] = {}

    for ruta in iterar_archivos_gdb(gdb):
        rel = ruta.relative_to(gdb).as_posix()
        st = ruta.stat()
        anterior = files_previos.get(rel) or {}
        if (
            anterior.get('sha256')
            and anterior.get('size') == st.st_size
            and anterior.get('mtime_ns') == st.st_mtime_ns
        ):
            sha = anterior['sha256']
        else:
            sha = _sha256_archivo(ruta)
        files[rel] = {
            'size': st.st_size,
            'mtime_ns': st.st_mtime_ns,
            'sha256': sha,
        }

    return {
        'version': METADATA_VERSION,
        'source': str(gdb.resolve()),
        'layer': capa,
        'geo_capa_zonas_env': geo_capa_env,
        'simplify_tolerance_m': SIMPLIFY_TOLERANCE_M,
        'files': files,
    }


def cargar_metadata_geo(cache_path: Path | None = None) -> dict | None:
    meta_path = ruta_metadata(cache_path)
    if not meta_path.is_file():
        return None
    try:
        return json.loads(meta_path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None


def guardar_metadata_geo(cache_path: Path, metadata: dict) -> None:
    escribir_json_atomico(ruta_metadata(cache_path), metadata)


def _contenido_ficheros(files: dict | None) -> dict:
    # mtime solo sirve para no recalcular hashes; un touch no debe forzar export.
    return {
        rel: (info.get('size'), info.get('sha256'))
        for rel, info in (files or {}).items()
        if isinstance(info, dict)
    }


def _huella_coincide(actual: dict, guardada: dict) -> bool:
    for clave in (
        'version',
        'source',
        'layer',
        'geo_capa_zonas_env',
        'simplify_tolerance_m',
    ):
        if actual.get(clave) != guardada.get(clave):
            return False
    return _contenido_ficheros(actual.get('files')) == _contenido_ficheros(guardada.get('files'))


def necesita_regenerar_geo(
    gdb_path: Path | None = None,
    cache_path: Path | None = None,
) -> bool:
    cache = cache_path or ruta_cache()
    if not cache.is_file():
        return True

    metadata = cargar_metadata_geo(cache)
    if metadata is None or 'files' not in metadata:
        return True

    gdb = resolver_ruta_gdb(gdb_path) if gdb_path is not None else ruta_gdb()
    if not gdb.exists() or not _parece_file_geodatabase(gdb):
        return False

    actual = huella_gdb(gdb, previa=metadata)
    return not _huella_coincide(actual, metadata)


def normalizar_nombre(texto: str) -> str:
    if not texto:
        return ''
    limpio = unicodedata.normalize('NFKD', str(texto))
    limpio = ''.join(c for c in limpio if not unicodedata.combining(c))
    limpio = limpio.lower()
    limpio = re.sub(r'[^a-z0-9]+', ' ', limpio)
    return ' '.join(limpio.split())


def _indice_embalses_mvp() -> dict[str, str]:
    return {normalizar_nombre(nombre): nombre for nombre in EMBALSES_OPCION_A}


def embalse_en_lista_mvp(nombre: str | None) -> str | None:
    if not nombre:
        return None
    clave = normalizar_nombre(nombre)
    return _indice_embalses_mvp().get(clave)


def _nombre_desde_fila(fila: gpd.GeoSeries) -> str | None:
    for columna in COLUMNAS_NOMBRE:
        if columna in fila.index:
            valor = fila[columna]
            if valor is not None and str(valor).strip():
                return str(valor).strip()
    for columna, valor in fila.items():
        if columna == 'geometry':
            continue
        if isinstance(valor, str) and valor.strip():
            clave = columna.lower()
            if any(pista in clave for pista in ('nom', 'emb', 'zona', 'name')):
                return valor.strip()
    return None


def _listar_capas(gdb_path: Path) -> list[tuple[str, str | None]]:
    import pyogrio

    capas = pyogrio.list_layers(str(gdb_path))
    resultado: list[tuple[str, str | None]] = []
    for capa in capas:
        if hasattr(capa, '__len__') and not isinstance(capa, (str, bytes)):
            nombre = str(capa[0])
            geom = str(capa[1]) if len(capa) > 1 else None
        else:
            nombre = str(capa)
            geom = None
        resultado.append((nombre, geom))
    return resultado


def _es_poligono(geom_tipo: str | None) -> bool:
    if not geom_tipo:
        return True
    tipo = str(geom_tipo).lower()
    return 'polygon' in tipo or 'multipolygon' in tipo or 'curve' in tipo


def detectar_capa_zonas(gdb_path: Path, capa_forzada: str | None = None) -> str:
    if capa_forzada:
        return capa_forzada

    capa_env = os.getenv('GEO_CAPA_ZONAS', '').strip()
    if capa_env:
        return capa_env

    capas = _listar_capas(gdb_path)
    if not capas:
        raise RuntimeError(f'No se encontraron capas en {gdb_path}')

    candidatas: list[str] = []
    poligonales: list[str] = []
    for nombre, geom in capas:
        if _es_poligono(geom):
            poligonales.append(nombre)
            upper = nombre.upper()
            if 'ZONA' in upper or 'NAVEG' in upper or 'EMBALS' in upper:
                candidatas.append(nombre)

    if len(candidatas) == 1:
        return candidatas[0]
    if len(candidatas) > 1:
        return candidatas[0]
    if len(poligonales) == 1:
        return poligonales[0]

    nombres = ', '.join(n for n, _ in capas)
    raise RuntimeError(
        'No se pudo detectar automáticamente la capa de zonas. '
        f'Capas disponibles: {nombres}. '
        'Define GEO_CAPA_ZONAS con el nombre exacto.'
    )


def exportar_geodata(
    gdb_path: Path | None = None,
    cache_path: Path | None = None,
    capa: str | None = None,
) -> Path:
    gdb = resolver_ruta_gdb(gdb_path) if gdb_path is not None else ruta_gdb()
    destino = cache_path or ruta_cache()

    if not gdb.exists():
        raise FileNotFoundError(f'No se encontró el geodatabase: {gdb}')
    if not _parece_file_geodatabase(gdb):
        raise RuntimeError(
            f'La ruta no parece un File Geodatabase válido: {gdb}. '
            'Si el Anexo 3 viene empaquetado, apunta a la carpeta '
            '`EMBALSES_NAVEGABILIDAD.gdb` anidada.'
        )

    capa_elegida = detectar_capa_zonas(gdb, capa_forzada=capa)
    gdf = gpd.read_file(str(gdb), layer=capa_elegida, engine='pyogrio')

    if gdf.empty:
        raise RuntimeError(f"La capa '{capa_elegida}' no contiene geometrías.")

    if gdf.crs is None:
        gdf = gdf.set_crs('EPSG:25829')
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    gdf_proj = gdf.to_crs(epsg=25830)
    gdf_proj = gdf_proj.copy()
    gdf_proj['geometry'] = gdf_proj.geometry.simplify(
        tolerance=SIMPLIFY_TOLERANCE_M,
        preserve_topology=True,
    )
    gdf = gdf_proj.to_crs(epsg=4326)

    with escritura_atomica(destino) as tmp:
        gdf.to_file(tmp, driver='GeoJSON')

    meta = {
        **huella_gdb(gdb, layer=capa_elegida),
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'features': len(gdf),
        'crs': 'EPSG:4326',
    }
    guardar_metadata_geo(destino, meta)

    return destino


def cache_disponible(cache_path: Path | None = None) -> bool:
    return (cache_path or ruta_cache()).is_file()


def cargar_zonas(cache_path: Path | None = None) -> gpd.GeoDataFrame:
    ruta = cache_path or ruta_cache()
    if not ruta.is_file():
        raise FileNotFoundError(
            f'No existe el cache geográfico en {ruta}. '
            'Asegura que el seed haya extraído docs_pack/ y que el lifespan '
            'haya regenerado geo_cache/.'
        )
    gdf = gpd.read_file(ruta)
    if gdf.crs is None:
        gdf = gdf.set_crs('EPSG:4326')
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    return gdf


def preparar_zonas(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Añade ``_nombre``, ``_area_m2`` e índices de nombres. Idempotente."""
    if '_nombre' in gdf.columns and 'indice_nombres' in gdf.attrs:
        return gdf

    zonas = gdf.copy()
    zonas['_nombre'] = [_nombre_desde_fila(fila) for _, fila in gdf.iterrows()]
    try:
        zonas['_area_m2'] = zonas.geometry.to_crs(epsg=CRS_METRICO).area
    except Exception:
        zonas['_area_m2'] = zonas.geometry.area

    indice: dict[str, list] = {}
    for idx, nombre in zonas['_nombre'].items():
        if nombre:
            indice.setdefault(normalizar_nombre(nombre), []).append(idx)
    zonas.attrs['indice_nombres'] = indice
    zonas.attrs['nombres_ordenados'] = sorted(
        {n for n in zonas['_nombre'] if n},
        key=normalizar_nombre,
    )
    return zonas


def geojson_para_mapa(gdf: gpd.GeoDataFrame, tolerancia_m: float = 25.0) -> dict:
    gdf = preparar_zonas(gdf).drop(columns=['_area_m2'])
    if gdf.empty:
        return json.loads(gdf.to_json())

    gdf_proj = gdf.to_crs(epsg=25830).copy()
    gdf_proj['geometry'] = gdf_proj.geometry.simplify(tolerance=tolerancia_m, preserve_topology=True)
    gdf_display = gdf_proj.to_crs(epsg=4326)
    return json.loads(gdf_display.to_json())


def nombre_feature_geojson(props: dict | None) -> str:
    if not props:
        return ''
    valor = props.get('_nombre')
    if valor is not None and str(valor).strip():
        return str(valor).strip()
    for clave in COLUMNAS_NOMBRE:
        valor = props.get(clave)
        if valor is not None and str(valor).strip():
            return str(valor).strip()
    return ''


def feature_por_nombre(geojson_data: dict, nombre: str | None) -> dict | None:
    if not nombre or not geojson_data:
        return None
    clave = normalizar_nombre(nombre)
    if not clave:
        return None
    for feature in geojson_data.get('features') or []:
        props = feature.get('properties') if isinstance(feature, dict) else None
        if normalizar_nombre(nombre_feature_geojson(props)) == clave:
            return feature
    return None


def geojson_highlight(feature: dict | None) -> dict:
    if feature is None:
        return {'type': 'FeatureCollection', 'features': []}
    return {'type': 'FeatureCollection', 'features': [feature]}


def _resultado_vacio(
    mensaje: str,
    *,
    lat: float | None = None,
    lon: float | None = None,
) -> dict:
    return {
        'encontrado': False,
        'nombre': None,
        'embalse_mvp': None,
        'en_lista_mvp': False,
        'atributos': {},
        'mensaje': mensaje,
        'bounds': None,
        'indice': None,
        'lat': float(lat) if lat is not None else None,
        'lon': float(lon) if lon is not None else None,
    }


def _sanitize_attr_value(valor):
    """Convert attribute values to JSON-friendly Python scalars."""
    if valor is None:
        return None
    if hasattr(valor, 'item'):
        try:
            valor = valor.item()
        except (ValueError, AttributeError):
            pass
    if isinstance(valor, float):
        if valor != valor or valor in (float('inf'), float('-inf')):  # NaN / inf
            return None
        return float(valor)
    if isinstance(valor, (bool, int, str)):
        return valor
    if hasattr(valor, 'isoformat'):
        try:
            return valor.isoformat()
        except Exception:
            return str(valor)
    try:
        import math

        if isinstance(valor, (int, float)) or (
            hasattr(valor, '__float__') and not isinstance(valor, (str, bytes, bool))
        ):
            fval = float(valor)
            if math.isnan(fval) or math.isinf(fval):
                return None
    except (TypeError, ValueError):
        pass
    if isinstance(valor, (bytes, bytearray)):
        return None
    try:
        # Reject nested geometry-like objects
        if hasattr(valor, 'geom_type'):
            return None
    except Exception:
        return None
    try:
        json.dumps(valor)
        return valor
    except (TypeError, ValueError, OverflowError):
        return str(valor)


def _atributos_desde_fila(fila: gpd.GeoSeries) -> dict:
    atributos = {}
    for col in fila.index:
        if col in ('geometry', '_area', '_area_m2', '_nombre') or fila[col] is None:
            continue
        sanitized = _sanitize_attr_value(fila[col])
        if sanitized is None and fila[col] is not None:
            continue
        atributos[str(col)] = sanitized
    return atributos


def _indice_seguro(indice) -> int | str | None:
    if indice is None:
        return None
    try:
        if hasattr(indice, 'item'):
            indice = indice.item()
    except (ValueError, AttributeError):
        pass
    try:
        return int(indice)
    except (TypeError, ValueError):
        return str(indice)


def _resultado_desde_fila(fila: gpd.GeoSeries, indice) -> dict:
    if '_nombre' in fila.index:
        nombre = fila['_nombre'] or None
    else:
        nombre = _nombre_desde_fila(fila)
    embalse_mvp = embalse_en_lista_mvp(nombre)
    atributos = _atributos_desde_fila(fila)

    try:
        geom = fila.geometry
        if geom is None or geom.is_empty:
            raise ValueError('empty geometry')
        minx, miny, maxx, maxy = geom.bounds
        bounds = [float(minx), float(miny), float(maxx), float(maxy)]
        centroide = geom.centroid
        lat = float(centroide.y)
        lon = float(centroide.x)
    except Exception:
        return _resultado_vacio(
            f'Zona «{nombre or "sin nombre"}» encontrada, pero su geometría no es válida.'
        )

    if embalse_mvp:
        mensaje = (
            f'Zona detectada: {nombre or "sin nombre"}. '
            f'Coincide con el embalse «{embalse_mvp}» de la lista del formulario MVP.'
        )
    elif nombre:
        mensaje = (
            f'Zona detectada: {nombre}. '
            'No coincide con ningún embalse de la lista MVP (opción A, plazo ≤ 1 año).'
        )
    else:
        mensaje = 'Zona detectada, pero sin nombre identificable en los atributos.'

    return {
        'encontrado': True,
        'nombre': nombre,
        'embalse_mvp': embalse_mvp,
        'en_lista_mvp': embalse_mvp is not None,
        'atributos': atributos,
        'mensaje': mensaje,
        'bounds': bounds,
        'indice': _indice_seguro(indice),
        'lat': lat,
        'lon': lon,
    }


def consultar_punto(
    lat: float,
    lon: float,
    gdf: gpd.GeoDataFrame | None = None,
) -> dict:
    zonas = preparar_zonas(gdf if gdf is not None else cargar_zonas())

    try:
        posiciones = zonas.sindex.query(Point(lon, lat), predicate='intersects')
        coincidencias = zonas.iloc[sorted(posiciones)]
    except Exception:
        return _resultado_vacio(
            'No se pudo consultar el punto (error espacial).',
            lat=lat,
            lon=lon,
        )

    if coincidencias.empty:
        return _resultado_vacio(
            'El punto no cae dentro de ninguna zona de navegación indexada.',
            lat=lat,
            lon=lon,
        )

    if len(coincidencias) > 1:
        coincidencias = coincidencias.sort_values('_area_m2', ascending=True, kind='stable')

    idx = coincidencias.index[0]
    return _resultado_desde_fila(coincidencias.loc[idx], idx)


def listar_nombres_zonas(gdf: gpd.GeoDataFrame) -> list[str]:
    return list(preparar_zonas(gdf).attrs['nombres_ordenados'])


def buscar_por_nombre(
    nombre: str,
    gdf: gpd.GeoDataFrame | None = None,
) -> dict:
    zonas = preparar_zonas(gdf if gdf is not None else cargar_zonas())
    clave = normalizar_nombre(nombre)
    if not clave:
        return _resultado_vacio('Indica un nombre de embalse o zona para buscar.')

    indices = zonas.attrs['indice_nombres'].get(clave)
    if not indices:
        return _resultado_vacio(f'No se encontró ninguna zona con el nombre «{nombre}».')

    coincidencias = zonas.loc[indices]
    if len(coincidencias) > 1:
        coincidencias = coincidencias.sort_values('_area_m2', ascending=True, kind='stable')

    idx = coincidencias.index[0]
    return _resultado_desde_fila(coincidencias.loc[idx], idx)


def bounds_wgs84(gdf: gpd.GeoDataFrame) -> tuple[float, float, float, float]:
    minx, miny, maxx, maxy = gdf.total_bounds
    return float(minx), float(miny), float(maxx), float(maxy)


def _modo_regenerar() -> str:
    valor = os.getenv('REGENERAR_GEO_ON_START', 'auto').strip().lower()
    if valor in ('never', 'always'):
        return valor
    return 'auto'


def regenerar_geo_si_cambio() -> dict:
    """Regenera geo_cache/ según REGENERAR_GEO_ON_START. Seguro para lifespan."""
    gdb = resolver_ruta_gdb()
    cache = ruta_cache()
    modo = _modo_regenerar()

    if modo == 'never':
        msg = 'REGENERAR_GEO_ON_START=never: no se comprueba ni regenera geo_cache/.'
        log.info(msg)
        return {'ok': True, 'action': 'skipped', 'message': msg, 'cache': str(cache)}

    gdb_valido = gdb.exists() and _parece_file_geodatabase(gdb)
    if not gdb_valido:
        if cache.is_file():
            msg = f'No hay GDB válido en {gdb}; se conserva {cache}.'
            log.info(msg)
            return {'ok': True, 'action': 'kept_cache', 'message': msg, 'cache': str(cache)}
        msg = f'No hay GDB válido en {gdb} ni cache; el mapa no estará disponible.'
        log.warning(msg)
        return {'ok': False, 'action': 'missing', 'message': msg, 'cache': str(cache)}

    # Varios workers pueden arrancar a la vez: solo uno exporta; el resto vuelve
    # a comprobar la huella tras obtener el lock y encuentra el cache al día.
    with lock_regeneracion('geo_cache'):
        if modo == 'auto' and not necesita_regenerar_geo(gdb, cache):
            msg = f'Sin cambios en el .gdb; {cache.parent}/ está actualizado.'
            log.info(msg)
            return {'ok': True, 'action': 'up_to_date', 'message': msg, 'cache': str(cache)}

        try:
            destino = exportar_geodata(gdb_path=gdb, cache_path=cache)
        except Exception as exc:
            msg = f'No se pudo regenerar geo_cache/: {exc}'
            log.exception(msg)
            return {'ok': False, 'action': 'error', 'message': msg, 'cache': str(cache)}

    msg = f'GeoJSON generado en {destino}'
    log.info(msg)
    return {'ok': True, 'action': 'exported', 'message': msg, 'cache': str(destino)}
