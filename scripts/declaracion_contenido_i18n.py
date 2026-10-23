#!/usr/bin/env python3
"""Sync the Declaración form content (Spanish keys) into the locale translation.json files.

The backend schema (titles, labels, help, options) and the validation error
templates are written in Spanish and the frontend uses them directly as i18n
keys. Option values are still submitted in Spanish, so the DOCX is unaffected.

Keys are read from backend/open_webui/navegacion/formulario_dr.py with `ast`
(no backend import needed). The script fails if a key has no translation or a
translation no longer matches any key.

Locales:
- en-US, en-GB, gl-ES, pt-PT, pt-BR get real translations.
- es-ES, ca-ES, eu-ES get the Spanish key itself. Without it they would fall
  back to en-US (English), since returnEmptyString is false.
- Any other locale falls back to en-US.

Usage: python3 scripts/declaracion_contenido_i18n.py [--force] [--check]
  --force  overwrite existing non-empty values
  --check  only verify keys/translations, do not write
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOCALES_DIR = REPO / 'src' / 'lib' / 'i18n' / 'locales'
FORMULARIO = REPO / 'backend' / 'open_webui' / 'navegacion' / 'formulario_dr.py'

LOCALES_IDENTIDAD = ('es-ES', 'ca-ES', 'eu-ES')

# Spanish key -> (en, gl, pt-PT, pt-BR or None when equal to pt-PT)
TRADUCCIONES: dict[str, tuple[str, str, str, str | None]] = {
    # --- Step titles
    'Datos del declarante': ('Declarant details', 'Datos do declarante', 'Dados do declarante', None),
    'Datos de la embarcación': ('Vessel details', 'Datos da embarcación', 'Dados da embarcação', None),
    'Seguro': ('Insurance', 'Seguro', 'Seguro', None),
    'Usuario y actividad': (
        'User and activity',
        'Usuario e actividade',
        'Utilizador e atividade',
        'Usuário e atividade',
    ),
    'Lugar de navegación': ('Navigation area', 'Lugar de navegación', 'Local de navegação', None),
    'Plazo de la declaración': ('Declaration period', 'Prazo da declaración', 'Prazo da declaração', None),
    'Documentación y firma': (
        'Documentation and signature',
        'Documentación e sinatura',
        'Documentação e assinatura',
        None,
    ),
    'Revisión y generación': ('Review and generate', 'Revisión e xeración', 'Revisão e geração', None),
    # --- Field labels
    'Tipo de declarante': ('Declarant type', 'Tipo de declarante', 'Tipo de declarante', None),
    'Nombre y apellidos o razón social': (
        'Full name or company name',
        'Nome e apelidos ou razón social',
        'Nome completo ou denominação social',
        'Nome completo ou razão social',
    ),
    'DNI / NIF / NIE / Pasaporte': (
        'ID card / Tax ID / Foreigner ID / Passport',
        'DNI / NIF / NIE / Pasaporte',
        'DNI / NIF / NIE / Passaporte',
        None,
    ),
    'Vía pública': ('Street', 'Vía pública', 'Via pública', None),
    'Número': ('Number', 'Número', 'Número', None),
    'Bloque': ('Block', 'Bloque', 'Bloco', None),
    'Escalera': ('Staircase', 'Escaleira', 'Escada', None),
    'Planta / piso': ('Floor', 'Planta / andar', 'Andar', None),
    'Puerta / letra': ('Door / letter', 'Porta / letra', 'Porta / letra', None),
    'Código postal': ('Postal code', 'Código postal', 'Código postal', 'CEP / código postal'),
    'Municipio': ('Municipality', 'Concello', 'Município', None),
    'Provincia': ('Province', 'Provincia', 'Província', None),
    'Localidad': ('Town', 'Localidade', 'Localidade', None),
    'País': ('Country', 'País', 'País', None),
    'Correo electrónico': ('Email', 'Correo electrónico', 'Correio eletrónico', 'E-mail'),
    'Teléfono': ('Phone', 'Teléfono', 'Telefone', None),
    'Forma de notificación': ('Notification method', 'Forma de notificación', 'Forma de notificação', None),
    '¿La embarcación ya estaba declarada?': (
        'Was the vessel already declared?',
        'A embarcación xa estaba declarada?',
        'A embarcação já estava declarada?',
        None,
    ),
    'Matrícula CHMS ya asignada': (
        'CHMS registration already assigned',
        'Matrícula CHMS xa asignada',
        'Matrícula CHMS já atribuída',
        None,
    ),
    'Nº correlativo de la embarcación': (
        'Vessel sequence number',
        'N.º correlativo da embarcación',
        'N.º sequencial da embarcação',
        None,
    ),
    'Tipo de embarcación': ('Vessel type', 'Tipo de embarcación', 'Tipo de embarcação', None),
    'Marca / modelo': ('Make / model', 'Marca / modelo', 'Marca / modelo', None),
    'Material del casco': ('Hull material', 'Material do casco', 'Material do casco', None),
    'Número de serie': ('Serial number', 'Número de serie', 'Número de série', None),
    'Eslora': ('Length overall', 'Eslora', 'Comprimento', None),
    'Manga': ('Beam', 'Manga', 'Boca', None),
    'Número máximo de ocupantes': (
        'Maximum number of occupants',
        'Número máximo de ocupantes',
        'Número máximo de ocupantes',
        None,
    ),
    'Altura del mástil (si tiene vela)': (
        'Mast height (if sailing)',
        'Altura do mastro (se ten vela)',
        'Altura do mastro (se tiver vela)',
        None,
    ),
    'Número de motores': ('Number of engines', 'Número de motores', 'Número de motores', None),
    'Tipo de motor': ('Engine type', 'Tipo de motor', 'Tipo de motor', None),
    'Marca del motor': ('Engine make', 'Marca do motor', 'Marca do motor', None),
    'Potencia (CV)': ('Power (hp)', 'Potencia (CV)', 'Potência (cv)', None),
    'Ciclo del motor': ('Engine cycle', 'Ciclo do motor', 'Ciclo do motor', None),
    'Número de póliza': ('Policy number', 'Número de póliza', 'Número da apólice', None),
    'Vigencia desde': ('Valid from', 'Vixencia desde', 'Válido desde', None),
    'Vigencia hasta': ('Valid until', 'Vixencia ata', 'Válido até', None),
    'Tipo de usuario': ('User type', 'Tipo de usuario', 'Tipo de utilizador', 'Tipo de usuário'),
    'Tipo de actividad': ('Activity type', 'Tipo de actividade', 'Tipo de atividade', None),
    'Describe la actividad': ('Describe the activity', 'Describe a actividade', 'Descreva a atividade', None),
    'Embalses en los que se solicita navegar': (
        'Reservoirs where navigation is requested',
        'Encoros nos que se solicita navegar',
        'Albufeiras onde se solicita navegar',
        'Reservatórios onde se solicita navegar',
    ),
    'Otros embalses no listados (opcional)': (
        'Other reservoirs not listed (optional)',
        'Outros encoros non listados (opcional)',
        'Outras albufeiras não listadas (opcional)',
        'Outros reservatórios não listados (opcional)',
    ),
    'Modalidad del plazo': ('Period type', 'Modalidade do prazo', 'Modalidade do prazo', None),
    'Año': ('Year', 'Ano', 'Ano', None),
    'Meses solicitados': ('Requested months', 'Meses solicitados', 'Meses solicitados', None),
    'Fecha desde': ('From date', 'Data desde', 'Data de início', None),
    'Fecha hasta': ('To date', 'Data ata', 'Data de fim', None),
    'Me opongo a que la Confederación consulte de oficio mis datos de identidad': (
        'I object to the Confederation checking my identity data on its own initiative',
        'Opóñome a que a Confederación consulte de oficio os meus datos de identidade',
        'Oponho-me a que a Confederação consulte oficiosamente os meus dados de identidade',
        'Eu me oponho a que a Confederação consulte de ofício meus dados de identidade',
    ),
    'Lugar de la firma': ('Place of signature', 'Lugar da sinatura', 'Local da assinatura', None),
    'Fecha de la firma': ('Date of signature', 'Data da sinatura', 'Data da assinatura', None),
    'Nombre de quien firma': ('Name of signatory', 'Nome de quen asina', 'Nome de quem assina', None),
    'DNI de quien firma': ("Signatory's ID number", 'DNI de quen asina', 'DNI de quem assina', None),
    # --- Help texts
    'Las personas jurídicas y entidades públicas reciben la notificación por medios electrónicos.': (
        'Legal entities and public bodies receive notifications electronically.',
        'As persoas xurídicas e entidades públicas reciben a notificación por medios electrónicos.',
        'As pessoas coletivas e entidades públicas recebem a notificação por meios eletrónicos.',
        'As pessoas jurídicas e entidades públicas recebem a notificação por meios eletrônicos.',
    ),
    'Formato CHMS-123-X-001.': ('Format CHMS-123-X-001.', 'Formato CHMS-123-X-001.', 'Formato CHMS-123-X-001.', None),
    '1 para la primera embarcación, 2 para la segunda, etc.': (
        '1 for the first vessel, 2 for the second, and so on.',
        '1 para a primeira embarcación, 2 para a segunda, etc.',
        '1 para a primeira embarcação, 2 para a segunda, etc.',
        None,
    ),
    'Ejemplo: 4,5 m': ('Example: 4.5 m', 'Exemplo: 4,5 m', 'Exemplo: 4,5 m', None),
    'Ejemplo: 1,8 m': ('Example: 1.8 m', 'Exemplo: 1,8 m', 'Exemplo: 1,8 m', None),
    'Lista de embalses con plazo máximo de 1 año. No se incluyen los embalses del régimen NRP (hasta 6 años).': (
        'Reservoirs with a maximum period of 1 year. Reservoirs under the NRP regime (up to 6 years) are not included.',
        'Lista de encoros con prazo máximo de 1 ano. Non se inclúen os encoros do réxime NRP (ata 6 anos).',
        'Lista de albufeiras com prazo máximo de 1 ano. Não se incluem as albufeiras do regime NRP (até 6 anos).',
        'Lista de reservatórios com prazo máximo de 1 ano. Não estão incluídos os reservatórios do regime NRP (até 6 anos).',
    ),
    # --- Options
    'PERSONA FÍSICA': ('INDIVIDUAL', 'PERSOA FÍSICA', 'PESSOA SINGULAR', 'PESSOA FÍSICA'),
    'PERSONA JURÍDICA': ('LEGAL ENTITY', 'PERSOA XURÍDICA', 'PESSOA COLETIVA', 'PESSOA JURÍDICA'),
    'ENTIDAD PÚBLICA': ('PUBLIC BODY', 'ENTIDADE PÚBLICA', 'ENTIDADE PÚBLICA', None),
    'Empresa': ('Company', 'Empresa', 'Empresa', None),
    'Club/federación': ('Club/federation', 'Club/federación', 'Clube/federação', None),
    'Particular': ('Private individual', 'Particular', 'Particular', None),
    'Entidad Pública': ('Public body', 'Entidade pública', 'Entidade pública', None),
    'Deportiva': ('Sports', 'Deportiva', 'Desportiva', 'Esportiva'),
    'Recreativa': ('Recreational', 'Recreativa', 'Recreativa', None),
    'Transporte': ('Transport', 'Transporte', 'Transporte', None),
    'Alquiler': ('Rental', 'Aluguer', 'Aluguer', 'Aluguel'),
    'Cursillos': ('Courses', 'Cursiños', 'Cursos', None),
    'Salvamento o vigilancia': ('Rescue or surveillance', 'Salvamento ou vixilancia', 'Salvamento ou vigilância', None),
    'Estudios científicos': ('Scientific studies', 'Estudos científicos', 'Estudos científicos', None),
    'Militares': ('Military', 'Militares', 'Militares', None),
    'Prueba o descenso puntual': ('One-off event or descent', 'Proba ou descenso puntual', 'Prova ou descida pontual', None),
    'Transporte madera': ('Timber transport', 'Transporte de madeira', 'Transporte de madeira', None),
    'Otros': ('Other', 'Outros', 'Outros', None),
    '2 tiempos': ('2-stroke', '2 tempos', '2 tempos', None),
    '4 tiempos': ('4-stroke', '4 tempos', '4 tempos', None),
    'Eléctrico': ('Electric', 'Eléctrico', 'Elétrico', None),
    'Medios electrónicos': ('Electronic means', 'Medios electrónicos', 'Meios eletrónicos', 'Meios eletrônicos'),
    'Papel': ('Paper', 'Papel', 'Papel', None),
    'Embarcación no declarada anteriormente': (
        'Vessel not previously declared',
        'Embarcación non declarada anteriormente',
        'Embarcação não declarada anteriormente',
        None,
    ),
    'Embarcación declarada anteriormente': (
        'Vessel previously declared',
        'Embarcación declarada anteriormente',
        'Embarcação declarada anteriormente',
        None,
    ),
    'Todo el año': ('Whole year', 'Todo o ano', 'Todo o ano', None),
    'Meses concretos': ('Specific months', 'Meses concretos', 'Meses específicos', None),
    'Fechas concretas': ('Specific dates', 'Datas concretas', 'Datas específicas', None),
    'Enero': ('January', 'Xaneiro', 'Janeiro', None),
    'Febrero': ('February', 'Febreiro', 'Fevereiro', None),
    'Marzo': ('March', 'Marzo', 'Março', None),
    'Abril': ('April', 'Abril', 'Abril', None),
    'Mayo': ('May', 'Maio', 'Maio', None),
    'Junio': ('June', 'Xuño', 'Junho', None),
    'Julio': ('July', 'Xullo', 'Julho', None),
    'Agosto': ('August', 'Agosto', 'Agosto', None),
    'Septiembre': ('September', 'Setembro', 'Setembro', None),
    'Octubre': ('October', 'Outubro', 'Outubro', None),
    'Noviembre': ('November', 'Novembro', 'Novembro', None),
    'Diciembre': ('December', 'Decembro', 'Dezembro', None),
    '— No aplica —': ('— Not applicable —', '— Non aplica —', '— Não se aplica —', None),
    # --- MVP scope notice
    (
        'Esta versión cubre: declarante (sin representante), dirección desglosada, notificación '
        '(siempre al declarante), una embarcación, seguro genérico, usuario/actividad, embalses de '
        'la lista con plazo máximo de 1 año, plazo en esa misma modalidad, y firma. No incluye '
        'todavía: persona representante, varias embarcaciones, navegación en ríos, el régimen NRP '
        'de hasta 6 años, ni las distintas variantes de seguro. Revisa siempre el documento '
        'generado antes de presentarlo.'
    ): (
        'This version covers: declarant (no representative), itemised address, notification (always '
        'to the declarant), one vessel, generic insurance, user/activity, listed reservoirs with a '
        'maximum period of 1 year, a period of that same type, and signature. It does not yet '
        'include: representative, several vessels, river navigation, the NRP regime of up to 6 '
        'years, or the different insurance variants. Always review the generated document before '
        'submitting it.',
        'Esta versión cobre: declarante (sen representante), enderezo desagregado, notificación '
        '(sempre ao declarante), unha embarcación, seguro xenérico, usuario/actividade, encoros da '
        'lista con prazo máximo de 1 ano, prazo nesa mesma modalidade, e sinatura. Aínda non '
        'inclúe: persoa representante, varias embarcacións, navegación en ríos, o réxime NRP de ata '
        '6 anos, nin as distintas variantes de seguro. Revisa sempre o documento xerado antes de '
        'presentalo.',
        'Esta versão abrange: declarante (sem representante), morada detalhada, notificação (sempre '
        'ao declarante), uma embarcação, seguro genérico, utilizador/atividade, albufeiras da lista '
        'com prazo máximo de 1 ano, prazo nessa mesma modalidade, e assinatura. Ainda não inclui: '
        'pessoa representante, várias embarcações, navegação em rios, o regime NRP de até 6 anos, '
        'nem as diferentes variantes de seguro. Reveja sempre o documento gerado antes de o '
        'apresentar.',
        'Esta versão abrange: declarante (sem representante), endereço detalhado, notificação '
        '(sempre ao declarante), uma embarcação, seguro genérico, usuário/atividade, reservatórios da '
        'lista com prazo máximo de 1 ano, prazo nessa mesma modalidade, e assinatura. Ainda não '
        'inclui: pessoa representante, várias embarcações, navegação em rios, o regime NRP de até 6 '
        'anos, nem as diferentes variantes de seguro. Sempre revise o documento gerado antes de '
        'apresentá-lo.',
    ),
    # --- Validation errors ({{...}} placeholders must be kept)
    '«{{campo}}» es obligatorio.': (
        '“{{campo}}” is required.',
        '«{{campo}}» é obrigatorio.',
        '«{{campo}}» é obrigatório.',
        None,
    ),
    '«{{campo}}» debe ser un texto.': (
        '“{{campo}}” must be text.',
        '«{{campo}}» debe ser un texto.',
        '«{{campo}}» deve ser um texto.',
        None,
    ),
    '«{{campo}}» no puede superar {{max}} caracteres.': (
        '“{{campo}}” cannot exceed {{max}} characters.',
        '«{{campo}}» non pode superar {{max}} caracteres.',
        '«{{campo}}» não pode exceder {{max}} caracteres.',
        None,
    ),
    '«{{campo}}» tiene un valor no permitido: {{valor}}.': (
        '“{{campo}}” has a value that is not allowed: {{valor}}.',
        '«{{campo}}» ten un valor non permitido: {{valor}}.',
        '«{{campo}}» tem um valor não permitido: {{valor}}.',
        None,
    ),
    '«{{campo}}» contiene valores no permitidos: {{valores}}.': (
        '“{{campo}}” contains values that are not allowed: {{valores}}.',
        '«{{campo}}» contén valores non permitidos: {{valores}}.',
        '«{{campo}}» contém valores não permitidos: {{valores}}.',
        None,
    ),
    '«{{campo}}» debe ser una lista de opciones.': (
        '“{{campo}}” must be a list of options.',
        '«{{campo}}» debe ser unha lista de opcións.',
        '«{{campo}}» deve ser uma lista de opções.',
        None,
    ),
    '«{{campo}}» no es una fecha válida.': (
        '“{{campo}}” is not a valid date.',
        '«{{campo}}» non é unha data válida.',
        '«{{campo}}» não é uma data válida.',
        None,
    ),
    '«{{campo}}» debe ser un número entero.': (
        '“{{campo}}” must be a whole number.',
        '«{{campo}}» debe ser un número enteiro.',
        '«{{campo}}» deve ser um número inteiro.',
        None,
    ),
    '«{{campo}}» debe estar entre {{min}} y {{max}}.': (
        '“{{campo}}” must be between {{min}} and {{max}}.',
        '«{{campo}}» debe estar entre {{min}} e {{max}}.',
        '«{{campo}}» deve estar entre {{min}} e {{max}}.',
        None,
    ),
    '«{{campo}}» debe marcarse o desmarcarse.': (
        '“{{campo}}” must be checked or unchecked.',
        '«{{campo}}» debe marcarse ou desmarcarse.',
        '«{{campo}}» deve ser marcado ou desmarcado.',
        None,
    ),
    'El correo electrónico del declarante no parece válido.': (
        "The declarant's email address does not look valid.",
        'O correo electrónico do declarante non parece válido.',
        'O endereço de correio eletrónico do declarante não parece válido.',
        'O e-mail do declarante não parece válido.',
    ),
    'La letra del DNI/NIE no coincide con el número. Revisa el documento.': (
        'The DNI/NIE letter does not match the number. Check the document.',
        'A letra do DNI/NIE non coincide co número. Revisa o documento.',
        'A letra do DNI/NIE não corresponde ao número. Verifique o documento.',
        None,
    ),
    'La letra del DNI/NIE de quien firma no coincide con el número. Revisa el documento.': (
        "The signatory's DNI/NIE letter does not match the number. Check the document.",
        'A letra do DNI/NIE de quen asina non coincide co número. Revisa o documento.',
        'A letra do DNI/NIE de quem assina não corresponde ao número. Verifique o documento.',
        None,
    ),
    'La matrícula debe tener el formato CHMS-123-X-001.': (
        'The registration must follow the format CHMS-123-X-001.',
        'A matrícula debe ter o formato CHMS-123-X-001.',
        'A matrícula deve ter o formato CHMS-123-X-001.',
        None,
    ),
    'La vigencia del seguro «desde» debe ser anterior a «hasta».': (
        'The insurance “from” date must be before the “until” date.',
        'A vixencia do seguro «desde» debe ser anterior a «ata».',
        'A data «desde» do seguro deve ser anterior à data «até».',
        None,
    ),
    'La fecha «desde» del plazo debe ser anterior a la fecha «hasta».': (
        'The period “from” date must be before the “to” date.',
        'A data «desde» do prazo debe ser anterior á data «ata».',
        'A data «desde» do prazo deve ser anterior à data «até».',
        None,
    ),
    'El plazo no puede superar un año (como máximo hasta el {{limite}}).': (
        'The period cannot exceed one year (until {{limite}} at the latest).',
        'O prazo non pode superar un ano (como máximo ata o {{limite}}).',
        'O prazo não pode exceder um ano (no máximo até {{limite}}).',
        None,
    ),
    'El año del plazo debe tener 4 dígitos (por ejemplo {{ejemplo}}).': (
        'The period year must have 4 digits (for example {{ejemplo}}).',
        'O ano do prazo debe ter 4 díxitos (por exemplo {{ejemplo}}).',
        'O ano do prazo deve ter 4 dígitos (por exemplo {{ejemplo}}).',
        None,
    ),
    'El año del plazo debe ser {{min}} o {{max}}.': (
        'The period year must be {{min}} or {{max}}.',
        'O ano do prazo debe ser {{min}} ou {{max}}.',
        'O ano do prazo deve ser {{min}} ou {{max}}.',
        None,
    ),
    'No se pudo determinar la matrícula de la embarcación. Revisa el documento y los datos de la embarcación.': (
        "The vessel's registration could not be determined. Check the document and the vessel details.",
        'Non se puido determinar a matrícula da embarcación. Revisa o documento e os datos da embarcación.',
        'Não foi possível determinar a matrícula da embarcação. Verifique o documento e os dados da embarcação.',
        None,
    ),
    'El seguro (del {{desde}} al {{hasta}}) no cubre todo el plazo declarado. Sin cubrir: {{tramos}}.': (
        'The insurance (from {{desde}} to {{hasta}}) does not cover the whole declared period. Not covered: {{tramos}}.',
        'O seguro (do {{desde}} ao {{hasta}}) non cobre todo o prazo declarado. Sen cubrir: {{tramos}}.',
        'O seguro (de {{desde}} a {{hasta}}) não cobre todo o prazo declarado. Sem cobertura: {{tramos}}.',
        None,
    ),
}


def _valores_por_locale(en: str, gl: str, pt_pt: str, pt_br: str | None) -> dict[str, str]:
    return {'en-US': en, 'en-GB': en, 'gl-ES': gl, 'pt-PT': pt_pt, 'pt-BR': pt_br or pt_pt}


def claves_formulario(path: Path = FORMULARIO) -> set[str]:
    """User-facing Spanish strings of the form schema and validation errors."""
    tree = ast.parse(path.read_text(encoding='utf-8'))
    constantes: dict[str, object] = {}
    for nodo in tree.body:
        if isinstance(nodo, (ast.Assign, ast.AnnAssign)):
            destinos = nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]
            for destino in destinos:
                if isinstance(destino, ast.Name) and nodo.value is not None:
                    constantes[destino.id] = nodo.value

    def texto(valor) -> str | None:
        if isinstance(valor, ast.Constant) and isinstance(valor.value, str):
            return valor.value
        if isinstance(valor, ast.Name):
            return texto(constantes.get(valor.id))
        return None

    def lista(valor) -> list[str]:
        if isinstance(valor, ast.Name):
            valor = constantes.get(valor.id)
        if isinstance(valor, ast.List):
            return [t for t in (texto(e) for e in valor.elts) if t is not None]
        return []

    claves: set[str] = set()
    for nodo in ast.walk(constantes['PASOS']):
        if not isinstance(nodo, ast.Dict):
            continue
        for k, v in zip(nodo.keys, nodo.values):
            nombre = k.value if isinstance(k, ast.Constant) else None
            if nombre in ('titulo', 'etiqueta', 'ayuda') and (t := texto(v)):
                claves.add(t)
            elif nombre == 'opciones':
                claves.update(lista(v))

    for nombre, valor in constantes.items():
        if nombre.startswith('E_') or nombre in ('LIMITACIONES_MVP', 'OPCION_VACIA'):
            if (t := texto(valor)) is not None:
                claves.add(t)

    for nodo in tree.body:
        if isinstance(nodo, ast.FunctionDef) and nodo.name == 'titulo_paso':
            for sub in ast.walk(nodo):
                if isinstance(sub, ast.Return) and (t := texto(sub.value)):
                    claves.add(t)
    return claves


def comprobar() -> list[str]:
    claves = claves_formulario()
    problemas = [f'sin traducción: {k!r}' for k in sorted(claves - TRADUCCIONES.keys())]
    problemas += [f'traducción huérfana: {k!r}' for k in sorted(TRADUCCIONES.keys() - claves)]
    for clave, valores in TRADUCCIONES.items():
        marcadores = sorted(set(_marcadores(clave)))
        for valor in filter(None, valores):
            if sorted(set(_marcadores(valor))) != marcadores:
                problemas.append(f'marcadores distintos en {valor!r} (clave {clave!r})')
    return problemas


def _marcadores(texto: str) -> list[str]:
    return re.findall(r'\{\{\s*(\w+)\s*\}\}', texto)


def sync_file(path: Path, locale: str, force: bool) -> int:
    if locale in LOCALES_IDENTIDAD:
        valores = {clave: clave for clave in TRADUCCIONES}
    else:
        valores = {}
        for clave, tupla in TRADUCCIONES.items():
            valor = _valores_por_locale(*tupla).get(locale)
            if valor:
                valores[clave] = valor
    if not valores:
        return 0

    data = json.loads(path.read_text(encoding='utf-8'))
    updated = 0
    for clave, valor in valores.items():
        actual = data.get(clave)
        if not force and actual not in (None, '', clave):
            continue
        if actual == valor:
            continue
        data[clave] = valor
        updated += 1

    if updated:
        path.write_text(json.dumps(data, ensure_ascii=False, indent='\t') + '\n', encoding='utf-8')
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--force', action='store_true', help='overwrite existing non-empty values')
    parser.add_argument('--check', action='store_true', help='only verify keys and translations')
    args = parser.parse_args()

    problemas = comprobar()
    if problemas:
        print('ERROR:', file=sys.stderr)
        for problema in problemas:
            print(f'  {problema}', file=sys.stderr)
        return 1
    print(f'{len(TRADUCCIONES)} keys, all translated')
    if args.check:
        return 0

    if not LOCALES_DIR.is_dir():
        print(f'Locales dir not found: {LOCALES_DIR}', file=sys.stderr)
        return 1
    total = 0
    for path in sorted(LOCALES_DIR.glob('*/translation.json')):
        n = sync_file(path, path.parent.name, args.force)
        if n:
            print(f'{path.parent.name}: updated {n} keys')
            total += n
    print(f'Done: {total} keys updated')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
