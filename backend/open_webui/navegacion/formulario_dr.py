"""Esquema, validación y contexto de plantilla de la Declaración Responsable (MVP).

Los pasos son declarativos y serializables a JSON (`mostrar_si` con reglas
``eq`` / ``neq`` / ``in``) para exponerlos vía ``GET /api/v1/declaracion/schema``.
"""

from __future__ import annotations

import copy
import re
from calendar import monthrange
from datetime import date, timedelta
from typing import Any

from open_webui.navegacion.constants import EMBALSES_OPCION_A

DECLARANTE_TIPOS = ['PERSONA FÍSICA', 'PERSONA JURÍDICA', 'ENTIDAD PÚBLICA']

USUARIO_TIPOS = ['Empresa', 'Club/federación', 'Particular', 'Entidad Pública']

ACTIVIDAD_TIPOS = [
    'Deportiva',
    'Recreativa',
    'Transporte',
    'Alquiler',
    'Cursillos',
    'Salvamento o vigilancia',
    'Estudios científicos',
    'Militares',
    'Prueba o descenso puntual',
    'Transporte madera',
    'Otros',
]

MOTOR_CICLOS = ['2 tiempos', '4 tiempos', 'Eléctrico']

NOTIFICACION_MEDIOS = ['Medios electrónicos', 'Papel']

EMBARCACION_YA_DECLARADA = 'Embarcación declarada anteriormente'
EMBARCACION_NUEVA = 'Embarcación no declarada anteriormente'
EMBARCACION_DECLARADA_OPCIONES = [EMBARCACION_NUEVA, EMBARCACION_YA_DECLARADA]

PLAZO_MODALIDADES = ['Todo el año', 'Meses concretos', 'Fechas concretas']

MESES = [
    'Enero',
    'Febrero',
    'Marzo',
    'Abril',
    'Mayo',
    'Junio',
    'Julio',
    'Agosto',
    'Septiembre',
    'Octubre',
    'Noviembre',
    'Diciembre',
]

PATRON_EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
OPCION_VACIA = '— No aplica —'
SEPARADOR_MATRICULA = '-'
LETRAS_CONTROL_DNI = 'TRWAGMYFPDXBNJZSQVHLCKE'
CORRELATIVO_MIN = 1
CORRELATIVO_MAX = 999
_ISO_FECHA = re.compile(r'^\d{4}-\d{2}-\d{2}$')

# Claves de tipo fecha (ISO en JSON → date en dominio).
CAMPOS_FECHA = frozenset(
    {
        'seguro_vigencia_desde',
        'seguro_vigencia_hasta',
        'plazo_fecha_desde',
        'plazo_fecha_hasta',
        'firma_fecha',
    }
)

PASOS: list[dict[str, Any]] = [
    {
        'titulo': 'Datos del declarante',
        'campos': [
            {
                'clave': 'declarante_tipo',
                'etiqueta': 'Tipo de declarante',
                'tipo': 'select',
                'opciones': DECLARANTE_TIPOS,
                'obligatorio': True,
            },
            {
                'clave': 'declarante_nombre',
                'etiqueta': 'Nombre y apellidos o razón social',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'declarante_dni',
                'etiqueta': 'DNI / NIF / NIE / Pasaporte',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'declarante_direccion',
                'etiqueta': 'Vía pública',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {'clave': 'declarante_numero', 'etiqueta': 'Número', 'tipo': 'texto', 'obligatorio': False},
            {'clave': 'declarante_bloque', 'etiqueta': 'Bloque', 'tipo': 'texto', 'obligatorio': False},
            {'clave': 'declarante_escalera', 'etiqueta': 'Escalera', 'tipo': 'texto', 'obligatorio': False},
            {
                'clave': 'declarante_planta',
                'etiqueta': 'Planta / piso',
                'tipo': 'texto',
                'obligatorio': False,
            },
            {
                'clave': 'declarante_puerta',
                'etiqueta': 'Puerta / letra',
                'tipo': 'texto',
                'obligatorio': False,
            },
            {
                'clave': 'declarante_cp',
                'etiqueta': 'Código postal',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'declarante_municipio',
                'etiqueta': 'Municipio',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'declarante_provincia',
                'etiqueta': 'Provincia',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'declarante_localidad',
                'etiqueta': 'Localidad',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'declarante_pais',
                'etiqueta': 'País',
                'tipo': 'texto',
                'obligatorio': True,
                'valor_inicial': 'España',
            },
            {
                'clave': 'declarante_email',
                'etiqueta': 'Correo electrónico',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'declarante_telefono',
                'etiqueta': 'Teléfono',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'notificacion_medio',
                'etiqueta': 'Forma de notificación',
                'tipo': 'select',
                'opciones': NOTIFICACION_MEDIOS,
                'obligatorio': True,
                'mostrar_si': {'eq': ['declarante_tipo', 'PERSONA FÍSICA']},
                'ayuda': (
                    'Las personas jurídicas y entidades públicas reciben la '
                    'notificación por medios electrónicos.'
                ),
            },
        ],
    },
    {
        'titulo': 'Datos de la embarcación',
        'campos': [
            {
                'clave': 'embarcacion_declarada_antes',
                'etiqueta': '¿La embarcación ya estaba declarada?',
                'tipo': 'select',
                'opciones': EMBARCACION_DECLARADA_OPCIONES,
                'obligatorio': True,
            },
            {
                'clave': 'embarcacion_matricula',
                'etiqueta': 'Matrícula CHMS ya asignada',
                'tipo': 'texto',
                'obligatorio': True,
                'mostrar_si': {'eq': ['embarcacion_declarada_antes', EMBARCACION_YA_DECLARADA]},
                'ayuda': 'Formato CHMS-123-X-001.',
            },
            {
                'clave': 'embarcacion_correlativo',
                'etiqueta': 'Nº correlativo de la embarcación',
                'tipo': 'numero',
                'obligatorio': True,
                'valor_inicial': CORRELATIVO_MIN,
                'minimo': CORRELATIVO_MIN,
                'maximo': CORRELATIVO_MAX,
                'mostrar_si': {'neq': ['embarcacion_declarada_antes', EMBARCACION_YA_DECLARADA]},
                'ayuda': '1 para la primera embarcación, 2 para la segunda, etc.',
            },
            {
                'clave': 'embarcacion_tipo',
                'etiqueta': 'Tipo de embarcación',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'embarcacion_marca_modelo',
                'etiqueta': 'Marca / modelo',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'embarcacion_material_casco',
                'etiqueta': 'Material del casco',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'embarcacion_numero_serie',
                'etiqueta': 'Número de serie',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'embarcacion_eslora',
                'etiqueta': 'Eslora',
                'tipo': 'texto',
                'obligatorio': True,
                'ayuda': 'Ejemplo: 4,5 m',
            },
            {
                'clave': 'embarcacion_manga',
                'etiqueta': 'Manga',
                'tipo': 'texto',
                'obligatorio': True,
                'ayuda': 'Ejemplo: 1,8 m',
            },
            {
                'clave': 'embarcacion_ocupantes_max',
                'etiqueta': 'Número máximo de ocupantes',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'embarcacion_vela_altura_mastil',
                'etiqueta': 'Altura del mástil (si tiene vela)',
                'tipo': 'texto',
                'obligatorio': False,
            },
            {
                'clave': 'embarcacion_motor_num_motores',
                'etiqueta': 'Número de motores',
                'tipo': 'texto',
                'obligatorio': False,
            },
            {
                'clave': 'embarcacion_motor_tipo',
                'etiqueta': 'Tipo de motor',
                'tipo': 'texto',
                'obligatorio': False,
            },
            {
                'clave': 'embarcacion_motor_marca',
                'etiqueta': 'Marca del motor',
                'tipo': 'texto',
                'obligatorio': False,
            },
            {
                'clave': 'embarcacion_motor_potencia_cv',
                'etiqueta': 'Potencia (CV)',
                'tipo': 'texto',
                'obligatorio': False,
            },
            {
                'clave': 'embarcacion_motor_ciclo',
                'etiqueta': 'Ciclo del motor',
                'tipo': 'select',
                'opciones': MOTOR_CICLOS,
                'obligatorio': False,
                'permite_vacio': True,
            },
        ],
    },
    {
        'titulo': 'Seguro',
        'campos': [
            {
                'clave': 'seguro_poliza',
                'etiqueta': 'Número de póliza',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'seguro_vigencia_desde',
                'etiqueta': 'Vigencia desde',
                'tipo': 'fecha',
                'obligatorio': True,
            },
            {
                'clave': 'seguro_vigencia_hasta',
                'etiqueta': 'Vigencia hasta',
                'tipo': 'fecha',
                'obligatorio': True,
            },
        ],
    },
    {
        'titulo': 'Usuario y actividad',
        'campos': [
            {
                'clave': 'usuario_tipo',
                'etiqueta': 'Tipo de usuario',
                'tipo': 'select',
                'opciones': USUARIO_TIPOS,
                'obligatorio': True,
            },
            {
                'clave': 'actividad_tipo',
                'etiqueta': 'Tipo de actividad',
                'tipo': 'select',
                'opciones': ACTIVIDAD_TIPOS,
                'obligatorio': True,
            },
            {
                'clave': 'actividad_otros',
                'etiqueta': 'Describe la actividad',
                'tipo': 'texto',
                'obligatorio': True,
                'mostrar_si': {'eq': ['actividad_tipo', 'Otros']},
            },
        ],
    },
    {
        'titulo': 'Lugar de navegación',
        'campos': [
            {
                'clave': 'embalses_seleccionados',
                'etiqueta': 'Embalses en los que se solicita navegar',
                'tipo': 'multiselect',
                'opciones': EMBALSES_OPCION_A,
                'obligatorio': True,
                'ayuda': (
                    'Lista de embalses con plazo máximo de 1 año. '
                    'No se incluyen los embalses del régimen NRP (hasta 6 años).'
                ),
            },
            {
                'clave': 'embalses_otros',
                'etiqueta': 'Otros embalses no listados (opcional)',
                'tipo': 'texto',
                'obligatorio': False,
            },
        ],
    },
    {
        'titulo': 'Plazo de la declaración',
        'campos': [
            {
                'clave': 'plazo_modalidad',
                'etiqueta': 'Modalidad del plazo',
                'tipo': 'select',
                'opciones': PLAZO_MODALIDADES,
                'obligatorio': True,
            },
            {
                'clave': 'plazo_anio',
                'etiqueta': 'Año',
                'tipo': 'texto',
                'obligatorio': True,
                'mostrar_si': {'in': ['plazo_modalidad', ['Todo el año', 'Meses concretos']]},
            },
            {
                'clave': 'plazo_meses',
                'etiqueta': 'Meses solicitados',
                'tipo': 'multiselect',
                'opciones': MESES,
                'obligatorio': True,
                'mostrar_si': {'eq': ['plazo_modalidad', 'Meses concretos']},
            },
            {
                'clave': 'plazo_fecha_desde',
                'etiqueta': 'Fecha desde',
                'tipo': 'fecha',
                'obligatorio': True,
                'mostrar_si': {'eq': ['plazo_modalidad', 'Fechas concretas']},
            },
            {
                'clave': 'plazo_fecha_hasta',
                'etiqueta': 'Fecha hasta',
                'tipo': 'fecha',
                'obligatorio': True,
                'mostrar_si': {'eq': ['plazo_modalidad', 'Fechas concretas']},
            },
        ],
    },
    {
        'titulo': 'Documentación y firma',
        'campos': [
            {
                'clave': 'oposicion_consulta_chms',
                'etiqueta': (
                    'Me opongo a que la Confederación consulte de oficio '
                    'mis datos de identidad'
                ),
                'tipo': 'checkbox',
                'obligatorio': False,
            },
            {
                'clave': 'firma_lugar',
                'etiqueta': 'Lugar de la firma',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'firma_fecha',
                'etiqueta': 'Fecha de la firma',
                'tipo': 'fecha',
                'obligatorio': True,
                'inicial_hoy': True,
            },
            {
                'clave': 'firma_nombre',
                'etiqueta': 'Nombre de quien firma',
                'tipo': 'texto',
                'obligatorio': True,
            },
            {
                'clave': 'firma_dni',
                'etiqueta': 'DNI de quien firma',
                'tipo': 'texto',
                'obligatorio': True,
            },
        ],
    },
]

TOTAL_PASOS_DATOS = len(PASOS)
NUM_PASO_REVISION = TOTAL_PASOS_DATOS + 1
TOTAL_PASOS = NUM_PASO_REVISION

LIMITACIONES_MVP = (
    'Esta versión cubre: declarante (sin representante), dirección '
    'desglosada, notificación (siempre al declarante), una embarcación, '
    'seguro genérico, usuario/actividad, embalses de la lista con plazo '
    'máximo de 1 año, plazo en esa misma modalidad, y firma. No incluye '
    'todavía: persona representante, varias embarcaciones, navegación en '
    'ríos, el régimen NRP de hasta 6 años, ni las distintas variantes de '
    'seguro. Revisa siempre el documento generado antes de presentarlo.'
)


def evaluar_mostrar_si(regla: dict | None, datos: dict) -> bool:
    """Evalúa una regla serializable ``{op: [clave, valor]}``."""
    if not regla:
        return True
    if 'eq' in regla:
        clave, esperado = regla['eq']
        return datos.get(clave) == esperado
    if 'neq' in regla:
        clave, esperado = regla['neq']
        return datos.get(clave) != esperado
    if 'in' in regla:
        clave, opciones = regla['in']
        return datos.get(clave) in (opciones or [])
    raise ValueError(f'Regla mostrar_si no soportada: {regla!r}')


def _parse_fecha(valor: Any) -> Any:
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str) and _ISO_FECHA.match(valor.strip()):
        try:
            return date.fromisoformat(valor.strip())
        except ValueError:
            return valor
    return valor


def normalizar_datos(datos: dict | None) -> dict:
    """Copia profunda con fechas ISO convertidas a ``date``. Idempotente."""
    resultado = copy.deepcopy(datos or {})
    for clave in CAMPOS_FECHA:
        if clave in resultado:
            resultado[clave] = _parse_fecha(resultado[clave])
    return resultado


def campos_paso(indice_paso: int, datos: dict) -> list[dict]:
    campos = PASOS[indice_paso - 1]['campos']
    return [c for c in campos if evaluar_mostrar_si(c.get('mostrar_si'), datos)]


def titulo_paso(indice_paso: int) -> str:
    if indice_paso == NUM_PASO_REVISION:
        return 'Revisión y generación'
    return PASOS[indice_paso - 1]['titulo']


def schema_pasos() -> list[dict]:
    """PASOS listos para JSON (sin callables)."""
    return copy.deepcopy(PASOS)


# --- Errores de validación -------------------------------------------------
# Cada error es serializable: ``codigo`` es la plantilla en español (y a la vez
# la clave i18n del frontend), ``params`` sus valores y ``mensaje`` el texto ya
# interpolado, útil para clientes sin i18n (curl, logs).

ErrorValidacion = dict[str, Any]

E_OBLIGATORIO = '«{{campo}}» es obligatorio.'
E_TIPO_TEXTO = '«{{campo}}» debe ser un texto.'
E_LONGITUD = '«{{campo}}» no puede superar {{max}} caracteres.'
E_VALOR_NO_PERMITIDO = '«{{campo}}» tiene un valor no permitido: {{valor}}.'
E_VALORES_NO_PERMITIDOS = '«{{campo}}» contiene valores no permitidos: {{valores}}.'
E_TIPO_LISTA = '«{{campo}}» debe ser una lista de opciones.'
E_FECHA_INVALIDA = '«{{campo}}» no es una fecha válida.'
E_NUMERO_INVALIDO = '«{{campo}}» debe ser un número entero.'
E_NUMERO_RANGO = '«{{campo}}» debe estar entre {{min}} y {{max}}.'
E_CHECKBOX = '«{{campo}}» debe marcarse o desmarcarse.'
E_EMAIL = 'El correo electrónico del declarante no parece válido.'
E_DNI_DECLARANTE = 'La letra del DNI/NIE no coincide con el número. Revisa el documento.'
E_DNI_FIRMA = 'La letra del DNI/NIE de quien firma no coincide con el número. Revisa el documento.'
E_MATRICULA_FORMATO = 'La matrícula debe tener el formato CHMS-123-X-001.'
E_SEGURO_ORDEN = 'La vigencia del seguro «desde» debe ser anterior a «hasta».'
E_PLAZO_ORDEN = 'La fecha «desde» del plazo debe ser anterior a la fecha «hasta».'
E_PLAZO_MAX_ANIO = 'El plazo no puede superar un año (como máximo hasta el {{limite}}).'
E_ANIO_FORMATO = 'El año del plazo debe tener 4 dígitos (por ejemplo {{ejemplo}}).'
E_ANIO_RANGO = 'El año del plazo debe ser {{min}} o {{max}}.'
E_MATRICULA_INDETERMINADA = (
    'No se pudo determinar la matrícula de la embarcación. '
    'Revisa el documento y los datos de la embarcación.'
)
E_SEGURO_COBERTURA = (
    'El seguro (del {{desde}} al {{hasta}}) no cubre todo el plazo declarado. Sin cubrir: {{tramos}}.'
)

MAX_LONGITUD_TEXTO = 500


def _error(codigo: str, **params: Any) -> ErrorValidacion:
    params_str = {clave: str(valor) for clave, valor in params.items()}
    mensaje = codigo
    for clave, valor in params_str.items():
        mensaje = mensaje.replace('{{' + clave + '}}', valor)
    return {'codigo': codigo, 'params': params_str, 'mensaje': mensaje}


def _hoy() -> date:
    return date.today()


def _sumar_un_anio(fecha: date) -> date:
    try:
        return fecha.replace(year=fecha.year + 1)
    except ValueError:  # 29 de febrero
        return fecha.replace(year=fecha.year + 1, day=28)


def _fmt(fecha: date) -> str:
    return fecha.strftime('%d/%m/%Y')


def _es_vacio(valor: Any) -> bool:
    if valor is None or valor == OPCION_VACIA:
        return True
    if isinstance(valor, str):
        return not valor.strip()
    if isinstance(valor, list):
        return len(valor) == 0
    return False


def _validar_campo(campo: dict, valor: Any) -> ErrorValidacion | None:
    """Validación genérica según ``tipo`` del esquema. ``valor`` ya normalizado."""
    etiqueta = campo['etiqueta']
    tipo = campo.get('tipo')
    opciones = campo.get('opciones') or []

    if _es_vacio(valor):
        return _error(E_OBLIGATORIO, campo=etiqueta) if campo.get('obligatorio') else None

    if tipo in ('texto', 'select'):
        if not isinstance(valor, str):
            return _error(E_TIPO_TEXTO, campo=etiqueta)
        if len(valor) > MAX_LONGITUD_TEXTO:
            return _error(E_LONGITUD, campo=etiqueta, max=MAX_LONGITUD_TEXTO)
        if tipo == 'select' and opciones and valor not in opciones:
            return _error(E_VALOR_NO_PERMITIDO, campo=etiqueta, valor=valor)
    elif tipo == 'multiselect':
        if not isinstance(valor, list) or not all(isinstance(item, str) for item in valor):
            return _error(E_TIPO_LISTA, campo=etiqueta)
        invalidos = [item for item in valor if opciones and item not in opciones]
        if invalidos:
            return _error(E_VALORES_NO_PERMITIDOS, campo=etiqueta, valores=', '.join(invalidos))
    elif tipo == 'fecha':
        if not isinstance(valor, date):
            return _error(E_FECHA_INVALIDA, campo=etiqueta)
    elif tipo == 'numero':
        if isinstance(valor, bool):
            return _error(E_NUMERO_INVALIDO, campo=etiqueta)
        try:
            numero = int(valor)
        except (TypeError, ValueError):
            return _error(E_NUMERO_INVALIDO, campo=etiqueta)
        if isinstance(valor, float) and not valor.is_integer():
            return _error(E_NUMERO_INVALIDO, campo=etiqueta)
        minimo, maximo = campo.get('minimo'), campo.get('maximo')
        if (minimo is not None and numero < minimo) or (maximo is not None and numero > maximo):
            return _error(E_NUMERO_RANGO, campo=etiqueta, min=minimo, max=maximo)
    elif tipo == 'checkbox':
        if not isinstance(valor, bool):
            return _error(E_CHECKBOX, campo=etiqueta)
    return None


def _validar_plazo(datos: dict) -> list[ErrorValidacion]:
    errores: list[ErrorValidacion] = []
    modalidad = datos.get('plazo_modalidad')

    if modalidad == 'Fechas concretas':
        desde, hasta = datos.get('plazo_fecha_desde'), datos.get('plazo_fecha_hasta')
        if isinstance(desde, date) and isinstance(hasta, date):
            limite = _sumar_un_anio(desde) - timedelta(days=1)
            if desde > hasta:
                errores.append(_error(E_PLAZO_ORDEN))
            elif hasta > limite:
                errores.append(_error(E_PLAZO_MAX_ANIO, limite=_fmt(limite)))

    if modalidad in ('Todo el año', 'Meses concretos'):
        anio = re.sub(r'\D', '', str(datos.get('plazo_anio') or ''))
        actual = _hoy().year
        if anio and len(anio) != 4:
            errores.append(_error(E_ANIO_FORMATO, ejemplo=actual))
        elif anio and not (actual <= int(anio) <= actual + 1):
            errores.append(_error(E_ANIO_RANGO, min=actual, max=actual + 1))

    return errores


def _validar_paso(indice_paso: int, datos: dict) -> list[ErrorValidacion]:
    """Igual que ``validar_paso`` pero con ``datos`` ya normalizados."""
    errores: list[ErrorValidacion] = []
    visibles = campos_paso(indice_paso, datos)
    claves = {campo['clave'] for campo in visibles}

    for campo in visibles:
        error = _validar_campo(campo, datos.get(campo['clave']))
        if error:
            errores.append(error)

    # Reglas cruzadas: se activan según los campos que contiene el paso, no por
    # su número, para que reordenar PASOS no las rompa.
    email = datos.get('declarante_email')
    if 'declarante_email' in claves and isinstance(email, str) and email and not PATRON_EMAIL.match(email):
        errores.append(_error(E_EMAIL))

    documento = datos.get('declarante_dni')
    if 'declarante_dni' in claves and isinstance(documento, str) and documento_valido(documento) is False:
        errores.append(_error(E_DNI_DECLARANTE))

    matricula = datos.get('embarcacion_matricula')
    if 'embarcacion_matricula' in claves and isinstance(matricula, str) and matricula and not matricula_valida(matricula):
        errores.append(_error(E_MATRICULA_FORMATO))

    if {'seguro_vigencia_desde', 'seguro_vigencia_hasta'} <= claves:
        desde, hasta = datos.get('seguro_vigencia_desde'), datos.get('seguro_vigencia_hasta')
        if isinstance(desde, date) and isinstance(hasta, date) and desde > hasta:
            errores.append(_error(E_SEGURO_ORDEN))

    if 'plazo_modalidad' in claves:
        errores.extend(_validar_plazo(datos))

    firma_dni = datos.get('firma_dni')
    if 'firma_dni' in claves and isinstance(firma_dni, str) and documento_valido(firma_dni) is False:
        errores.append(_error(E_DNI_FIRMA))

    return errores


def validar_paso(indice_paso: int, datos: dict) -> list[ErrorValidacion]:
    return _validar_paso(indice_paso, normalizar_datos(datos))


def _intervalos_plazo(datos: dict) -> list[tuple[date, date]]:
    modalidad = datos.get('plazo_modalidad')

    if modalidad == 'Fechas concretas':
        desde, hasta = datos.get('plazo_fecha_desde'), datos.get('plazo_fecha_hasta')
        if isinstance(desde, date) and isinstance(hasta, date):
            return [(desde, hasta)]
        return []

    digitos = re.sub(r'\D', '', str(datos.get('plazo_anio') or ''))
    if len(digitos) != 4:
        return []
    anio = int(digitos)

    if modalidad == 'Todo el año':
        return [(date(anio, 1, 1), date(anio, 12, 31))]

    if modalidad == 'Meses concretos':
        plazo_meses = datos.get('plazo_meses')
        meses = [MESES.index(m) + 1 for m in (plazo_meses if isinstance(plazo_meses, list) else []) if m in MESES]
        return [(date(anio, mes, 1), date(anio, mes, monthrange(anio, mes)[1])) for mes in sorted(meses)]

    return []


def intervalos_plazo(datos: dict) -> list[tuple[date, date]]:
    return _intervalos_plazo(normalizar_datos(datos))


def validar_global(datos: dict) -> list[ErrorValidacion]:
    errores: list[ErrorValidacion] = []
    datos = normalizar_datos(datos)

    for indice in range(1, TOTAL_PASOS_DATOS + 1):
        errores.extend(_validar_paso(indice, datos))

    if not matricula_efectiva(datos):
        errores.append(_error(E_MATRICULA_INDETERMINADA))

    desde = datos.get('seguro_vigencia_desde')
    hasta = datos.get('seguro_vigencia_hasta')
    if not (isinstance(desde, date) and isinstance(hasta, date)):
        # Ya reportado por la validación de campos (obligatorio / fecha inválida).
        return errores

    sin_cubrir = [(inicio, fin) for inicio, fin in _intervalos_plazo(datos) if inicio < desde or fin > hasta]
    if sin_cubrir:
        tramos = ', '.join(f'{_fmt(inicio)} a {_fmt(fin)}' for inicio, fin in sin_cubrir[:3])
        if len(sin_cubrir) > 3:
            tramos += ', ...'
        errores.append(_error(E_SEGURO_COBERTURA, desde=_fmt(desde), hasta=_fmt(hasta), tramos=tramos))

    return errores


def normalizar_documento(documento: str) -> str:
    return re.sub(r'[^0-9A-Za-z]', '', documento or '').upper()


def documento_valido(documento: str) -> bool | None:
    limpio = normalizar_documento(documento)
    if re.fullmatch(r'\d{8}[A-Z]', limpio):
        return limpio[-1] == LETRAS_CONTROL_DNI[int(limpio[:8]) % 23]
    if re.fullmatch(r'[XYZ]\d{7}[A-Z]', limpio):
        numero = str('XYZ'.index(limpio[0])) + limpio[1:8]
        return limpio[-1] == LETRAS_CONTROL_DNI[int(numero) % 23]
    return None


def letra_documento(documento: str) -> str:
    limpio = normalizar_documento(documento)
    if not limpio:
        return ''
    if limpio[-1].isalpha():
        return limpio[-1]
    if limpio[0].isalpha():
        return limpio[0]
    return ''


_SEPARADORES_MATRICULA = re.compile(r'[\s\-_./]')
_PATRON_MATRICULA = re.compile(r'CHMS(\d{3})([A-Z])(\d{3})', re.ASCII)


def normalizar_matricula(matricula: str) -> str:
    """Devuelve la matrícula en formato canónico ``CHMS-123-X-001`` o ``''`` si no es válida.

    Solo se toleran separadores habituales; cualquier otro carácter la invalida
    (así no se imprime en el documento algo distinto de lo validado).
    """
    limpio = _SEPARADORES_MATRICULA.sub('', matricula or '').upper()
    coincidencia = _PATRON_MATRICULA.fullmatch(limpio)
    if not coincidencia:
        return ''
    return SEPARADOR_MATRICULA.join(['CHMS', *coincidencia.groups()])


def matricula_valida(matricula: str) -> bool:
    return bool(normalizar_matricula(matricula))


def calcular_matricula(documento: str, correlativo: int = CORRELATIVO_MIN) -> str:
    limpio = normalizar_documento(documento)
    digitos = re.sub(r'\D', '', limpio)
    if len(digitos) < 3:
        raise ValueError(
            'El documento de identidad necesita al menos 3 dígitos para generar la matrícula.'
        )
    letra = letra_documento(limpio)
    if not letra:
        raise ValueError('No se pudo determinar la letra del documento de identidad.')
    try:
        numero = int(correlativo)
    except (TypeError, ValueError):
        numero = CORRELATIVO_MIN
    numero = max(CORRELATIVO_MIN, min(CORRELATIVO_MAX, numero))
    return SEPARADOR_MATRICULA.join(['CHMS', digitos[-3:], letra, f'{numero:03d}'])


def matricula_efectiva(datos: dict) -> str:
    if datos.get('embarcacion_declarada_antes') == EMBARCACION_YA_DECLARADA:
        return normalizar_matricula(str(datos.get('embarcacion_matricula') or ''))
    try:
        return calcular_matricula(
            str(datos.get('declarante_dni') or ''),
            datos.get('embarcacion_correlativo') or CORRELATIVO_MIN,
        )
    except ValueError:
        return ''


def _fmt_fecha(valor: Any) -> str:
    if isinstance(valor, date):
        return valor.strftime('%d/%m/%Y')
    return str(valor) if valor else ''


def construir_contexto_plantilla(datos: dict) -> dict:
    datos = normalizar_datos(datos)
    contexto = {campo['clave']: '' for paso in PASOS for campo in paso['campos']}
    contexto.update(datos)

    for clave in CAMPOS_FECHA:
        contexto[clave] = _fmt_fecha(contexto.get(clave))

    if not (contexto.get('declarante_pais') or '').strip():
        contexto['declarante_pais'] = 'España'

    if contexto.get('declarante_tipo') != 'PERSONA FÍSICA':
        contexto['notificacion_medio'] = 'Medios electrónicos'
    elif not contexto.get('notificacion_medio'):
        contexto['notificacion_medio'] = 'Medios electrónicos'

    digitos_anio = re.sub(r'\D', '', str(contexto.get('plazo_anio') or '').strip())
    contexto['plazo_anio_yy'] = digitos_anio[-2:] if digitos_anio else ''
    contexto['embarcacion_matricula'] = matricula_efectiva(contexto)
    contexto['plazo_meses'] = list(contexto.get('plazo_meses') or [])
    contexto['embalses_seleccionados'] = list(contexto.get('embalses_seleccionados') or [])
    contexto['oposicion_consulta_chms'] = bool(contexto.get('oposicion_consulta_chms'))

    for clave, valor in list(contexto.items()):
        if valor is None or valor == OPCION_VACIA:
            contexto[clave] = ''

    return contexto
