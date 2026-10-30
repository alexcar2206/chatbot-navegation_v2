from open_webui.navegacion.formulario_dr import _validar_campo


def test_validar_campo_incluye_clave():
    campo = {
        'clave': 'declarante_nombre',
        'etiqueta': 'Full name',
        'tipo': 'texto',
        'obligatorio': True,
    }
    err = _validar_campo(campo, '')
    assert err is not None
    assert err['params']['clave'] == 'declarante_nombre'
    assert err['params']['campo'] == 'Full name'


def test_validar_campo_opcional_vacio():
    campo = {
        'clave': 'embalses_otros',
        'etiqueta': 'Other reservoirs',
        'tipo': 'texto',
        'obligatorio': False,
    }
    assert _validar_campo(campo, '') is None
