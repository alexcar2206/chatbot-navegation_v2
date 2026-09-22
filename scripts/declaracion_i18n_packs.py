"""Translation packs for the Declaración Responsable UI chrome."""

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

ES_VALUES = dict(
	zip(
		DECLARACION_KEYS,
		(
			'Declaración',
			'Permitir a los usuarios generar declaraciones responsables de navegación (DOCX).',
			'Rellena la declaración responsable de navegación (MVP Miño-Sil) y descarga el DOCX oficial.',
			'La plantilla de declaración aún no está disponible. Espera al seed del docs_pack.',
			'No se pudo cargar el asistente de declaración',
			'Revisión y generación',
			'Paso',
			'de',
			'Anterior',
			'Siguiente',
			'Generar DOCX',
			'Generando…',
			'Declaración descargada',
			'Corrige los errores de validación antes de generar',
			'Matrícula que se generará',
			'Borradores',
			'Nombre del borrador',
			'Guardar borrador',
			'Borrador guardado',
			'Borrador cargado',
			'Borrador eliminado',
			'Aún no hay borradores en este navegador.',
			'Has alcanzado el máximo de borradores. Elimina uno antes de guardar otro.',
			'Cargar',
			'Eliminar',
			'Usar en el formulario',
			'Usar como otros embalses',
			'Cargando…',
		),
		strict=True,
	)
)

PACKS = {
	'en-US': EN_VALUES,
	'en-GB': EN_VALUES,
	'es-ES': ES_VALUES,
}


def get_translations(locale: str) -> dict[str, str]:
	return PACKS.get(locale) or EN_VALUES
