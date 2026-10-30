from open_webui.navegacion.borradores import (
    E_DEMASIADO_GRANDE,
    E_NOMBRE_VACIO,
    E_VALOR_INVALIDO,
    MAX_BYTES_DATOS,
    errores_borrador,
    preparar_borrador,
    sanitizar_datos,
)


def test_sanitizar_datos_descarta_desconocidas():
    limpios = sanitizar_datos(
        {
            'declarante_nombre': 'Ana',
            'campo_obsoleto': 'x',
            'otra_clave_vieja': 1,
        }
    )
    assert limpios == {'declarante_nombre': 'Ana'}


def test_sanitizar_datos_no_dict():
    assert sanitizar_datos(None) == {}  # type: ignore[arg-type]
    assert sanitizar_datos('x') == {}  # type: ignore[arg-type]


def test_preparar_borrador_sin_error_por_desconocidas():
    errores, limpios = preparar_borrador(
        'Mi borrador',
        1,
        {
            'declarante_nombre': 'Ana',
            'campo_que_ya_no_existe': 'valor',
        },
    )
    assert errores == []
    assert limpios == {'declarante_nombre': 'Ana'}
    assert 'campo_que_ya_no_existe' not in limpios


def test_preparar_borrador_sigue_fallando_tipo_invalido():
    errores, limpios = preparar_borrador(
        'Mi borrador',
        1,
        {
            'declarante_nombre': {'no': 'string'},
            'campo_obsoleto': 'se_descarta',
        },
    )
    assert limpios == {'declarante_nombre': {'no': 'string'}}
    assert any(e['codigo'] == E_VALOR_INVALIDO for e in errores)
    assert 'declarante_nombre' in next(e for e in errores if e['codigo'] == E_VALOR_INVALIDO)['claves']


def test_preparar_borrador_basura_grande_solo_en_desconocidas():
    basura = 'x' * (MAX_BYTES_DATOS + 1000)
    errores, limpios = preparar_borrador(
        'Ok',
        1,
        {
            'declarante_nombre': 'Ana',
            'campo_obsoleto_enorme': basura,
        },
    )
    assert errores == []
    assert limpios == {'declarante_nombre': 'Ana'}
    assert not any(e['codigo'] == E_DEMASIADO_GRANDE for e in errores)


def test_errores_borrador_nombre_vacio():
    errores = errores_borrador('', 1, {'declarante_nombre': 'Ana'})
    assert any(e['codigo'] == E_NOMBRE_VACIO for e in errores)
