from pathlib import Path

import pytest

from open_webui.navegacion.geozona import (
    _plazo_anios,
    _reparar_cp850,
    _restricciones_limpias,
    _texto_limpio,
    buscar_por_nombre,
    cargar_zonas,
    clasificar_navegacion,
    consultar_punto,
    geojson_para_mapa,
    preparar_zonas,
    resumen_estados,
)

FIXTURE = Path(__file__).parent / 'fixtures' / 'zonas_mini.geojson'


@pytest.fixture(scope='module')
def zonas():
    return preparar_zonas(cargar_zonas(FIXTURE))


@pytest.mark.parametrize(
    ('valor', 'esperado'),
    [
        ('Sí', 'permitida'),
        ('Sí condicionado', 'restringida'),
        ('Sólo remos y vela', 'restringida'),
        ('Sujeto a PONARS', 'ponars'),
        ('No', 'prohibida'),
        ('  sí  ', 'permitida'),
        ('Pendiente de revisión', None),
        (' ', None),
        (None, None),
    ],
)
def test_clasificar_navegacion(valor, esperado):
    assert clasificar_navegacion(valor) == esperado


def test_texto_limpio():
    assert _texto_limpio('Se permite la navegación a vela y a remo.  ') == (
        'Se permite la navegación a vela y a remo.'
    )
    assert _texto_limpio(' ') is None
    assert _texto_limpio('No procede') is None
    assert _texto_limpio(float('nan')) is None


def test_restricciones_limpias():
    assert _restricciones_limpias('Sin restricciones adiccionales') is None
    assert _restricciones_limpias('Está prohibida la navegación con moto acuática.') == (
        'Está prohibida la navegación con moto acuática.'
    )


@pytest.mark.parametrize(
    ('texto', 'esperado'),
    [
        ('El plazo máximo de vigencia de las declaraciones responsables es de un (1) año.', 1),
        ('El plazo máximo de vigencia de las declaraciones responsables es de seis (6) años.', 6),
        (None, None),
        ('Sin plazo indicado', None),
    ],
)
def test_plazo_anios(texto, esperado):
    assert _plazo_anios(texto) == esperado


@pytest.mark.parametrize(
    ('texto', 'esperado'),
    [
        ('MI¥O (LU)', 'MIÑO (LU)'),
        ('NOGUEIRA Y RAMUÖN (OR)', 'NOGUEIRA Y RAMUÍN (OR)'),
        ('PµRAMO-SIL (LE)', 'PÁRAMO-SIL (LE)'),
        ('PÁRAMO DEL SIL-TORENO (LE', 'PÁRAMO DEL SIL-TORENO (LE'),
        ('PONFERRADA (LE)', 'PONFERRADA (LE)'),
        (None, None),
    ],
)
def test_reparar_cp850(texto, esperado):
    assert _reparar_cp850(texto) == esperado


def test_preparar_zonas_anade_estado(zonas):
    # pandas puede representar el estado ausente como NaN en columnas de texto.
    estados = {n: (e if isinstance(e, str) else None) for n, e in zip(zonas['_nombre'], zonas['_estado'])}
    assert estados == {
        'ALBARELLOS': 'permitida',
        'PRADA': 'restringida',
        'BARCENA': 'restringida',
        'SANTO ESTEVO': 'ponars',
        'PEÑADRADA': 'prohibida',
        'SIN CLASIFICAR': None,
    }


def test_resumen_estados(zonas):
    recuento, desconocidos = resumen_estados(zonas)
    assert recuento == {'permitida': 1, 'restringida': 2, 'ponars': 1, 'prohibida': 1}
    assert desconocidos == ['Pendiente de revisión']


def test_consultar_punto_devuelve_ficha(zonas):
    res = consultar_punto(42.005, -7.995, gdf=zonas)

    assert res['encontrado'] is True
    assert res['nombre'] == 'ALBARELLOS'
    assert 'atributos' not in res
    assert res['navegacion'] == {
        'estado': 'permitida',
        'valor_origen': 'Sí',
        'condiciones': 'Se permite la navegación a vela, a remo y motor.',
        'restricciones': 'Está prohibida la navegación con moto acuática.',
        'plazo': 'El plazo máximo de vigencia de las declaraciones responsables es de seis (6) años.',
        'plazo_anios': 6,
    }
    assert res['embalse'] == {
        'rio': 'AVIA',
        'municipio': 'LEIRO Y BORBORAS (OR)',
        'usos': ['hidroelectrico'],
        'superficie_ha': 314.02,
        'volumen_hm3': 90.73,
        'titular': 'UNION FENOSA',
        'anio': 1971,
    }


def test_buscar_por_nombre_limpia_y_repara(zonas):
    barcena = buscar_por_nombre('Bárcena', gdf=zonas)
    assert barcena['navegacion']['estado'] == 'restringida'
    assert barcena['navegacion']['restricciones'] is None
    assert barcena['embalse']['usos'] == ['riego', 'abastecimiento', 'hidroelectrico']

    penadrada = buscar_por_nombre('Peñadrada', gdf=zonas)
    assert penadrada['navegacion']['estado'] == 'prohibida'
    assert penadrada['navegacion']['plazo'] is None
    assert penadrada['navegacion']['plazo_anios'] is None
    assert penadrada['embalse']['superficie_ha'] is None
    assert penadrada['embalse']['anio'] is None

    desconocida = buscar_por_nombre('Sin clasificar', gdf=zonas)
    assert desconocida['navegacion']['estado'] is None
    assert desconocida['navegacion']['condiciones'] is None
    assert desconocida['embalse'] == {
        'rio': None,
        'municipio': 'MIÑO (LU)',
        'usos': [],
        'superficie_ha': None,
        'volumen_hm3': None,
        'titular': None,
        'anio': None,
    }


def test_resultado_vacio_sin_ficha(zonas):
    res = consultar_punto(40.0, -3.0, gdf=zonas)
    assert res['encontrado'] is False
    assert res['navegacion'] is None
    assert res['embalse'] is None
    assert 'atributos' not in res


def test_geojson_para_mapa_incluye_props_filtro(zonas):
    data = geojson_para_mapa(zonas)
    features = data['features']
    assert features
    alb = next(f for f in features if f['properties'].get('_nombre') == 'ALBARELLOS')
    props = alb['properties']
    assert props['_estado'] == 'permitida'
    assert props['_rio'] == 'AVIA'
    assert props['_usos'] == ['hidroelectrico']
    assert props['_superficie_ha'] == 314.02
    assert props['_volumen_hm3'] == 90.73
    assert props['_plazo_anios'] == 6
    assert isinstance(props['_centroide'], list) and len(props['_centroide']) == 2
    assert '_mvp' in props
