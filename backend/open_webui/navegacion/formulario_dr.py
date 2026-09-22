"""Esquema, validación y contexto de plantilla de la Declaración Responsable (MVP).

Los pasos son declarativos y serializables a JSON (`mostrar_si` con reglas
``eq`` / ``neq`` / ``in``) para exponerlos vía ``GET /api/v1/declaracion/schema``.
"""

from __future__ import annotations

import copy
import re
from calendar import monthrange
from datetime import date
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
    """Copia profunda con fechas ISO convertidas a ``date``."""
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


def validar_paso(indice_paso: int, datos: dict) -> list[str]:
    errores: list[str] = []
    datos = normalizar_datos(datos)

    for campo in campos_paso(indice_paso, datos):
        valor = datos.get(campo['clave'])
        vacio = valor is None or (isinstance(valor, (str, list)) and len(valor) == 0)
        if campo.get('obligatorio') and vacio:
            errores.append(f'«{campo["etiqueta"]}» es obligatorio.')
            continue

        opciones = campo.get('opciones') or []
        tipo = campo.get('tipo')
        if tipo == 'select' and not vacio and opciones and valor not in opciones:
            errores.append(
                f'«{campo["etiqueta"]}» tiene un valor no permitido: {valor}.'
            )
        elif tipo == 'multiselect' and isinstance(valor, list) and opciones:
            invalidos = [item for item in valor if item not in opciones]
            if invalidos:
                errores.append(
                    f'«{campo["etiqueta"]}» contiene valores no permitidos: '
                    f'{", ".join(str(v) for v in invalidos)}.'
                )

    if indice_paso == 1:
        email = datos.get('declarante_email', '')
        if email and not PATRON_EMAIL.match(str(email)):
            errores.append('El correo electrónico del declarante no parece válido.')
        documento = datos.get('declarante_dni', '')
        if documento and documento_valido(str(documento)) is False:
            errores.append(
                'La letra del DNI/NIE no coincide con el número. Revisa el documento.'
            )

    if indice_paso == 2:
        if datos.get('embarcacion_declarada_antes') == EMBARCACION_YA_DECLARADA:
            matricula = datos.get('embarcacion_matricula', '')
            if matricula and not matricula_valida(str(matricula)):
                errores.append('La matrícula debe tener el formato CHMS-123-X-001.')
        else:
            correlativo = datos.get('embarcacion_correlativo')
            try:
                numero = int(correlativo) if correlativo not in (None, '') else None
            except (TypeError, ValueError):
                numero = None
                errores.append('El nº correlativo de la embarcación debe ser un número.')
            if numero is not None and not (CORRELATIVO_MIN <= numero <= CORRELATIVO_MAX):
                errores.append(
                    f'El nº correlativo de la embarcación debe estar entre '
                    f'{CORRELATIVO_MIN} y {CORRELATIVO_MAX}.'
                )

    if indice_paso == 3:
        desde, hasta = datos.get('seguro_vigencia_desde'), datos.get('seguro_vigencia_hasta')
        if isinstance(desde, date) and isinstance(hasta, date) and desde > hasta:
            errores.append('La vigencia del seguro «desde» debe ser anterior a «hasta».')

    if indice_paso == 6:
        if datos.get('plazo_modalidad') == 'Fechas concretas':
            desde, hasta = datos.get('plazo_fecha_desde'), datos.get('plazo_fecha_hasta')
            if isinstance(desde, date) and isinstance(hasta, date) and desde > hasta:
                errores.append(
                    'La fecha «desde» del plazo debe ser anterior a la fecha «hasta».'
                )
        anio = re.sub(r'\D', '', str(datos.get('plazo_anio') or ''))
        if datos.get('plazo_modalidad') in ('Todo el año', 'Meses concretos') and anio:
            if len(anio) != 4:
                errores.append('El año del plazo debe tener 4 dígitos (por ejemplo 2026).')

    if indice_paso == TOTAL_PASOS_DATOS:
        firma_dni = datos.get('firma_dni', '')
        if firma_dni and documento_valido(str(firma_dni)) is False:
            errores.append(
                'La letra del DNI/NIE de quien firma no coincide con el número. '
                'Revisa el documento.'
            )

    return errores


def intervalos_plazo(datos: dict) -> list[tuple[date, date]]:
    datos = normalizar_datos(datos)
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
        meses = [MESES.index(m) + 1 for m in (datos.get('plazo_meses') or []) if m in MESES]
        return [
            (date(anio, mes, 1), date(anio, mes, monthrange(anio, mes)[1]))
            for mes in sorted(meses)
        ]

    return []


def validar_global(datos: dict) -> list[str]:
    errores: list[str] = []
    datos = normalizar_datos(datos)

    for indice in range(1, TOTAL_PASOS_DATOS + 1):
        errores.extend(validar_paso(indice, datos))

    if not matricula_efectiva(datos):
        errores.append(
            'No se pudo determinar la matrícula de la embarcación. '
            'Revisa el documento y los datos de la embarcación.'
        )

    desde = datos.get('seguro_vigencia_desde')
    hasta = datos.get('seguro_vigencia_hasta')
    if not (isinstance(desde, date) and isinstance(hasta, date)):
        return errores

    sin_cubrir = [
        (inicio, fin)
        for inicio, fin in intervalos_plazo(datos)
        if inicio < desde or fin > hasta
    ]
    if sin_cubrir:
        tramos = ', '.join(
            f'{inicio:%d/%m/%Y} a {fin:%d/%m/%Y}' for inicio, fin in sin_cubrir[:3]
        )
        resto = ', ...' if len(sin_cubrir) > 3 else ''
        errores.append(
            f'El seguro (del {desde:%d/%m/%Y} al {hasta:%d/%m/%Y}) no cubre '
            f'todo el plazo declarado. Sin cubrir: {tramos}{resto}.'
        )

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


def matricula_valida(matricula: str) -> bool:
    limpio = re.sub(r'[^0-9A-Za-z]', '', (matricula or '')).upper()
    return bool(re.fullmatch(r'CHMS\d{3}[A-Z]\d{3}', limpio))


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
        return (datos.get('embarcacion_matricula') or '').strip()
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
