"""Complete translation packs for the Declaración Responsable UI chrome."""

DECLARACION_KEYS = (
	'Declaration',
	'Allow users to generate responsible navigation declarations (DOCX).',
	'Fill in the responsible navigation declaration (Miño-Sil MVP) and download the official DOCX.',
	'The declaration template is not available yet. Wait for the docs pack seed.',
	'Could not load the declaration wizard',
	'Review and generate',
	'Step',
	'of',
	'Previous',
	'Next',
	'Generate DOCX',
	'Generating…',
	'Declaration downloaded',
	'Fix validation errors before generating',
	'Registration that will be generated',
	'Drafts',
	'Draft name',
	'Save draft',
	'Draft saved',
	'Draft loaded',
	'Draft deleted',
	'No drafts saved in this browser yet.',
	'Maximum drafts reached. Delete one before saving another.',
	'Load',
	'Delete',
	'Use in declaration form',
	'Use as other reservoirs',
	'Loading…',
)

EN_VALUES = {key: key for key in DECLARACION_KEYS}


def _pack(values: tuple[str, ...]) -> dict[str, str]:
	"""Build a pack while making omissions fail at import time."""
	if len(values) != len(DECLARACION_KEYS):
		raise ValueError(f'Expected {len(DECLARACION_KEYS)} translations, got {len(values)}')
	return dict(zip(DECLARACION_KEYS, values, strict=True))


_EN = (
	'Declaration',
	'Allow users to generate responsible navigation declarations (DOCX).',
	'Fill in the responsible navigation declaration (Miño-Sil MVP) and download the official DOCX.',
	'The declaration template is not available yet. Wait for the docs pack seed.',
	'Could not load the declaration wizard',
	'Review and generate',
	'Step',
	'of',
	'Previous',
	'Next',
	'Generate DOCX',
	'Generating…',
	'Declaration downloaded',
	'Fix validation errors before generating',
	'Registration that will be generated',
	'Drafts',
	'Draft name',
	'Save draft',
	'Draft saved',
	'Draft loaded',
	'Draft deleted',
	'No drafts saved in this browser yet.',
	'Maximum drafts reached. Delete one before saving another.',
	'Load',
	'Delete',
	'Use in declaration form',
	'Use as other reservoirs',
	'Loading…',
)

PACKS = {'en-US': {'Declaration': 'Declaration',
           'Allow users to generate responsible navigation declarations (DOCX).': 'Allow users to generate responsible '
                                                                                  'navigation declarations (DOCX).',
           'Fill in the responsible navigation declaration (Miño-Sil MVP) and download the official DOCX.': 'Fill in '
                                                                                                            'the '
                                                                                                            'responsible '
                                                                                                            'navigation '
                                                                                                            'declaration '
                                                                                                            '(Miño-Sil '
                                                                                                            'MVP) and '
                                                                                                            'download '
                                                                                                            'the '
                                                                                                            'official '
                                                                                                            'DOCX.',
           'The declaration template is not available yet. Wait for the docs pack seed.': 'The declaration template is '
                                                                                          'not available yet. Wait for '
                                                                                          'the docs pack seed.',
           'Could not load the declaration wizard': 'Could not load the declaration wizard',
           'Review and generate': 'Review and generate',
           'Step': 'Step',
           'of': 'of',
           'Previous': 'Previous',
           'Next': 'Next',
           'Generate DOCX': 'Generate DOCX',
           'Generating…': 'Generating…',
           'Declaration downloaded': 'Declaration downloaded',
           'Fix validation errors before generating': 'Fix validation errors before generating',
           'Registration that will be generated': 'Registration that will be generated',
           'Drafts': 'Drafts',
           'Draft name': 'Draft name',
           'Save draft': 'Save draft',
           'Draft saved': 'Draft saved',
           'Draft loaded': 'Draft loaded',
           'Draft deleted': 'Draft deleted',
           'No drafts saved in this browser yet.': 'No drafts saved in this browser yet.',
           'Maximum drafts reached. Delete one before saving another.': 'Maximum drafts reached. Delete one before '
                                                                        'saving another.',
           'Load': 'Load',
           'Delete': 'Delete',
           'Use in declaration form': 'Use in declaration form',
           'Use as other reservoirs': 'Use as other reservoirs',
           'Loading…': 'Loading…'},
 'es-ES': {'Declaration': 'Declaración',
           'Allow users to generate responsible navigation declarations (DOCX).': 'Permitir a los usuarios generar '
                                                                                  'declaraciones responsables de '
                                                                                  'navegación (DOCX).',
           'Fill in the responsible navigation declaration (Miño-Sil MVP) and download the official DOCX.': 'Rellena '
                                                                                                            'la '
                                                                                                            'declaración '
                                                                                                            'responsable '
                                                                                                            'de '
                                                                                                            'navegación '
                                                                                                            '(MVP '
                                                                                                            'Miño-Sil) '
                                                                                                            'y '
                                                                                                            'descarga '
                                                                                                            'el DOCX '
                                                                                                            'oficial.',
           'The declaration template is not available yet. Wait for the docs pack seed.': 'La plantilla de declaración '
                                                                                          'aún no está disponible. '
                                                                                          'Espera al seed del '
                                                                                          'docs_pack.',
           'Could not load the declaration wizard': 'No se pudo cargar el asistente de declaración',
           'Review and generate': 'Revisión y generación',
           'Step': 'Paso',
           'of': 'de',
           'Previous': 'Anterior',
           'Next': 'Siguiente',
           'Generate DOCX': 'Generar DOCX',
           'Generating…': 'Generando…',
           'Declaration downloaded': 'Declaración descargada',
           'Fix validation errors before generating': 'Corrige los errores de validación antes de generar',
           'Registration that will be generated': 'Matrícula que se generará',
           'Drafts': 'Borradores',
           'Draft name': 'Nombre del borrador',
           'Save draft': 'Guardar borrador',
           'Draft saved': 'Borrador guardado',
           'Draft loaded': 'Borrador cargado',
           'Draft deleted': 'Borrador eliminado',
           'No drafts saved in this browser yet.': 'Aún no hay borradores en este navegador.',
           'Maximum drafts reached. Delete one before saving another.': 'Has alcanzado el máximo de borradores. '
                                                                        'Elimina uno antes de guardar otro.',
           'Load': 'Cargar',
           'Delete': 'Eliminar',
           'Use in declaration form': 'Usar en el formulario',
           'Use as other reservoirs': 'Usar como otros embalses',
           'Loading…': 'Cargando…'},
 'gl-ES': {'Declaration': 'Declaración',
           'Allow users to generate responsible navigation declarations (DOCX).': 'Permitir aos usuarios xerar '
                                                                                  'declaracións responsables de '
                                                                                  'navegación (DOCX).',
           'Fill in the responsible navigation declaration (Miño-Sil MVP) and download the official DOCX.': 'Enche a '
                                                                                                            'declaración '
                                                                                                            'responsable '
                                                                                                            'de '
                                                                                                            'navegación '
                                                                                                            '(MVP '
                                                                                                            'Miño-Sil) '
                                                                                                            'e '
                                                                                                            'descarga '
                                                                                                            'o DOCX '
                                                                                                            'oficial.',
           'The declaration template is not available yet. Wait for the docs pack seed.': 'A plantilla de declaración '
                                                                                          'aínda non está dispoñible. '
                                                                                          'Agarda ao seed do '
                                                                                          'docs_pack.',
           'Could not load the declaration wizard': 'Non se puido cargar o asistente de declaración',
           'Review and generate': 'Revisión e xeración',
           'Step': 'Paso',
           'of': 'de',
           'Previous': 'Anterior',
           'Next': 'Seguinte',
           'Generate DOCX': 'Xerar DOCX',
           'Generating…': 'Xerando…',
           'Declaration downloaded': 'Declaración descargada',
           'Fix validation errors before generating': 'Corrixe os erros de validación antes de xerar',
           'Registration that will be generated': 'Matrícula que se xerará',
           'Drafts': 'Borradores',
           'Draft name': 'Nome do borrador',
           'Save draft': 'Gardar borrador',
           'Draft saved': 'Borrador gardado',
           'Draft loaded': 'Borrador cargado',
           'Draft deleted': 'Borrador eliminado',
           'No drafts saved in this browser yet.': 'Aínda non hai borradores neste navegador.',
           'Maximum drafts reached. Delete one before saving another.': 'Alcanzaches o máximo de borradores. Elimina '
                                                                        'un antes de gardar outro.',
           'Load': 'Cargar',
           'Delete': 'Eliminar',
           'Use in declaration form': 'Usar no formulario',
           'Use as other reservoirs': 'Usar como outros encoros',
           'Loading…': 'Cargando…'},
 'pt-PT': {'Declaration': 'Declaração',
           'Allow users to generate responsible navigation declarations (DOCX).': 'Permitir aos utilizadores gerar '
                                                                                  'declarações responsáveis de '
                                                                                  'navegação (DOCX).',
           'Fill in the responsible navigation declaration (Miño-Sil MVP) and download the official DOCX.': 'Preencha '
                                                                                                            'a '
                                                                                                            'declaração '
                                                                                                            'responsável '
                                                                                                            'de '
                                                                                                            'navegação '
                                                                                                            '(MVP '
                                                                                                            'Miño-Sil) '
                                                                                                            'e '
                                                                                                            'descarregue '
                                                                                                            'o DOCX '
                                                                                                            'oficial.',
           'The declaration template is not available yet. Wait for the docs pack seed.': 'O modelo de declaração '
                                                                                          'ainda não está disponível. '
                                                                                          'Aguarde o seed do docs '
                                                                                          'pack.',
           'Could not load the declaration wizard': 'Não foi possível carregar o assistente de declaração',
           'Review and generate': 'Revisão e geração',
           'Step': 'Passo',
           'of': 'de',
           'Previous': 'Anterior',
           'Next': 'Seguinte',
           'Generate DOCX': 'Gerar DOCX',
           'Generating…': 'A gerar…',
           'Declaration downloaded': 'Declaração descarregada',
           'Fix validation errors before generating': 'Corrija os erros de validação antes de gerar',
           'Registration that will be generated': 'Matrícula que será gerada',
           'Drafts': 'Rascunhos',
           'Draft name': 'Nome do rascunho',
           'Save draft': 'Guardar rascunho',
           'Draft saved': 'Rascunho guardado',
           'Draft loaded': 'Rascunho carregado',
           'Draft deleted': 'Rascunho eliminado',
           'No drafts saved in this browser yet.': 'Ainda não há rascunhos guardados neste browser.',
           'Maximum drafts reached. Delete one before saving another.': 'Máximo de rascunhos atingido. Elimine um '
                                                                        'antes de guardar outro.',
           'Load': 'Carregar',
           'Delete': 'Eliminar',
           'Use in declaration form': 'Usar no formulário de declaração',
           'Use as other reservoirs': 'Usar como outros reservatórios',
           'Loading…': 'A carregar…'}}


# Keys added after the packs above. Locales without an entry get the English key.
EXTRA_TRANSLATIONS: dict[str, dict[str, str]] = {
	'Save as new draft': {
		'es-ES': 'Guardar como borrador nuevo',
		'gl-ES': 'Gardar como borrador novo',
		'pt-PT': 'Guardar como novo rascunho',
	},
	'Drafts are stored only in this browser and include personal data.': {
		'es-ES': 'Los borradores se guardan solo en este navegador e incluyen datos personales.',
		'gl-ES': 'Os borradores gárdanse só neste navegador e inclúen datos persoais.',
		'pt-PT': 'Os rascunhos são guardados apenas neste browser e incluem dados pessoais.',
	},
}

ALL_KEYS = DECLARACION_KEYS + tuple(EXTRA_TRANSLATIONS)


def get_translations(locale: str) -> dict[str, str]:
	pack = dict(PACKS.get(locale) or EN_VALUES)
	for key, values in EXTRA_TRANSLATIONS.items():
		pack[key] = values.get(locale, key)
	return pack
