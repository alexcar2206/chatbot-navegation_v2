"""Complete translation packs for the navigation map UI."""

MAPA_KEYS_CORE = (
	'Map',
	'Allow users to consult navigation zones on the map.',
	'Search reservoir / zone…',
	'Reservoir or zone',
	'Consult point',
	'Use my location',
	'Loading map…',
	'Lat',
	'Lon',
	'Zone',
	'MVP reservoir',
	'Centroid',
	'Click the map to query a zone. Coordinates use EPSG:4326.',
	'Consult the navigation zones of Annex 3 (Miño-Sil): search by name, click the map, coordinates, or your location.',
	'The map is not available yet. Wait for the docs pack seed and geo_cache generation.',
	'Could not load the map',
	'Failed to query map point',
	'Failed to search',
	'Enter valid latitude and longitude (EPSG:4326)',
	'Geolocation is not available in this browser',
	'Could not get your location',
	'Not in the MVP list (option A). For the declaration use “Other reservoirs”.',
)

MAPA_KEYS_EXTRA = (
	'Add to selection',
	'Add as other reservoirs',
	'Selected zones',
	'Clear selection',
	'Already in the selection',
	'Added to selection',
	'Remove',
)

MAPA_KEYS = MAPA_KEYS_CORE + MAPA_KEYS_EXTRA

EN_VALUES = {key: key for key in MAPA_KEYS}

ES_CORE_VALUES = (
	'Mapa',
	'Permitir a los usuarios consultar las zonas de navegación en el mapa.',
	'Buscar embalse / zona…',
	'Embalse o zona',
	'Consultar punto',
	'Usar mi ubicación',
	'Cargando mapa…',
	'Lat',
	'Lon',
	'Zona',
	'Embalse MVP',
	'Centroide',
	'Haz clic en el mapa para consultar la zona. Coordenadas en EPSG:4326.',
	'Consulta las zonas de navegación del Anexo 3 (Miño-Sil): búsqueda por nombre, clic en el mapa, coordenadas o tu ubicación.',
	'El mapa no está disponible todavía. Espera a que el seed extraiga docs_pack y se genere geo_cache/.',
	'No se pudo cargar el mapa',
	'Error al consultar el punto',
	'Error al buscar',
	'Introduce latitud y longitud válidas (EPSG:4326)',
	'Geolocalización no disponible en este navegador',
	'No se pudo obtener la ubicación',
	'No está en la lista MVP (opción A). Para la declaración usa «Otros embalses».',
)

ES_EXTRA_VALUES = (
	'Añadir a la selección',
	'Añadir como otros embalses',
	'Zonas seleccionadas',
	'Vaciar selección',
	'Ya está en la selección',
	'Añadido a la selección',
	'Eliminar',
)

ES_VALUES = dict(
	zip(
		MAPA_KEYS,
		ES_CORE_VALUES + ES_EXTRA_VALUES,
		strict=True,
	)
)

EXTRA_EN_VALUES = {key: key for key in MAPA_KEYS_EXTRA}
EXTRA_ES_VALUES = dict(zip(MAPA_KEYS_EXTRA, ES_EXTRA_VALUES, strict=True))


def _pack(values: tuple[str, ...]) -> dict[str, str]:
	"""Build a pack while making omissions fail at import time."""
	if len(values) != len(MAPA_KEYS_CORE):
		raise ValueError(f'Expected {len(MAPA_KEYS_CORE)} translations, got {len(values)}')
	return dict(zip(MAPA_KEYS_CORE, values, strict=True))


PACKS = {
	'en-US': _pack(
		(
			'Map',
			'Allow users to consult navigation zones on the map.',
			'Search reservoir / zone…',
			'Reservoir or zone',
			'Consult point',
			'Use my location',
			'Loading map…',
			'Lat',
			'Lon',
			'Zone',
			'MVP reservoir',
			'Centroid',
			'Click the map to query a zone. Coordinates use EPSG:4326.',
			'Consult the navigation zones of Annex 3 (Miño-Sil): search by name, click the map, coordinates, or your location.',
			'The map is not available yet. Wait for the docs pack seed and geo_cache generation.',
			'Could not load the map',
			'Failed to query map point',
			'Failed to search',
			'Enter valid latitude and longitude (EPSG:4326)',
			'Geolocation is not available in this browser',
			'Could not get your location',
			'Not in the MVP list (option A). For the declaration use “Other reservoirs”.',
		)
	),
	'es-ES': _pack(
		(
			'Mapa',
			'Permitir a los usuarios consultar las zonas de navegación en el mapa.',
			'Buscar embalse / zona…',
			'Embalse o zona',
			'Consultar punto',
			'Usar mi ubicación',
			'Cargando mapa…',
			'Lat',
			'Lon',
			'Zona',
			'Embalse MVP',
			'Centroide',
			'Haz clic en el mapa para consultar la zona. Coordenadas en EPSG:4326.',
			'Consulta las zonas de navegación del Anexo 3 (Miño-Sil): búsqueda por nombre, clic en el mapa, coordenadas o tu ubicación.',
			'El mapa no está disponible todavía. Espera a que el seed extraiga docs_pack y se genere geo_cache/.',
			'No se pudo cargar el mapa',
			'Error al consultar el punto',
			'Error al buscar',
			'Introduce latitud y longitud válidas (EPSG:4326)',
			'Geolocalización no disponible en este navegador',
			'No se pudo obtener la ubicación',
			'No está en la lista MVP (opción A). Para la declaración usa «Otros embalses».',
		)
	),
	'gl-ES': _pack(
		(
			'Mapa',
			'Permitir aos usuarios consultar zonas de navegación no mapa.',
			'Busca encoro/zona...',
			'Encoro ou zona',
			'Punto de consulta',
			'Usa a miña localización',
			'Cargando mapa…',
			'Lat',
			'Lon',
			'Zona',
			'Depósito de MVP',
			'Centroide',
			'Fai clic no mapa para consultar unha zona. As coordenadas usan EPSG:4326.',
			'Consulta as zonas de navegación do anexo 3 (Miño-Sil): busca por nome, fai clic no mapa, coordenadas ou a túa localización',
			'O mapa aínda non está dispoñible. Agarda ata a xeración de sementes e xeo_caché do paquete de documentos (docs_pack, geo_cache).',
			'Non se puido cargar o mapa',
			'Produciuse un erro ao consultar o punto do mapa',
			'Produciuse un erro ao buscar',
			'Introduce a latitude e lonxitude válidas (EPSG:4326)',
			'A xeolocalización non está dispoñible neste navegador',
			'Non se puido obter a túa localización',
			'Non está na lista de MVP (opción A). Para a declaración use "Outros encoros".',
		)
	),
	'pt-PT': _pack(
		(
			'Mapa',
			'Permitir aos utilizadores consultar zonas de navegação no mapa.',
			'Pesquisar reservatório / zona…',
			'Reservatório ou zona',
			'Ponto de consulta',
			'Usar a minha localização',
			'Carregando mapa…',
			'Lat.',
			'Lon',
			'Zona',
			'Reservatório MVP',
			'Centróide',
			'Clique no mapa para consultar uma zona. As coordenadas utilizam EPSG:4326.',
			'Consulte as zonas de navegação do Anexo 3 (Miño-Sil): pesquise por nome, clique no mapa, nas coordenadas ou na sua localização',
			'O mapa ainda não está disponível. Aguarde pela geração do seed do pacote de documentos e do geo_cache (docs_pack, geo_cache).',
			'Não foi possível carregar o mapa',
			'Falha ao consultar o ponto do mapa',
			'Falha ao pesquisar',
			'Introduza a latitude e a longitude válidas (EPSG:4326)',
			'A geolocalização não está disponível neste browser',
			'Não foi possível obter a sua localização',
			'Não está na lista de MVP (opção A). Para a declaração utilizar “Outros reservatórios”.',
		)
	),
}


def get_translations(locale: str) -> dict[str, str]:
	base = dict(PACKS.get(locale) or {key: key for key in MAPA_KEYS_CORE})
	extras = dict(EXTRA_ES_VALUES) if locale == 'es-ES' else dict(EXTRA_EN_VALUES)
	return {**base, **extras}
