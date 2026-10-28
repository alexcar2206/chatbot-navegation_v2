import { WEBUI_API_BASE_URL } from '$lib/constants';

export type ZonaEstado = 'permitida' | 'restringida' | 'prohibida' | 'ponars';

export type MapaNavegacion = {
	estado: ZonaEstado | null;
	valor_origen: string | null;
	condiciones: string | null;
	restricciones: string | null;
	plazo: string | null;
	plazo_anios: number | null;
};

export type MapaUsoEmbalse = 'hidroelectrico' | 'abastecimiento' | 'riego';

export type MapaEmbalse = {
	rio: string | null;
	municipio: string | null;
	usos: MapaUsoEmbalse[];
	superficie_ha: number | null;
	volumen_hm3: number | null;
	titular: string | null;
	anio: number | null;
};

export type MapaConsultaResult = {
	encontrado: boolean;
	nombre: string | null;
	embalse_mvp: string | null;
	en_lista_mvp: boolean;
	navegacion: MapaNavegacion | null;
	embalse: MapaEmbalse | null;
	mensaje: string;
	bounds: [number, number, number, number] | null;
	indice: number | null;
	lat: number | null;
	lon: number | null;
};

export type MapaStatus = {
	available: boolean;
	/** Only returned to admins. */
	cache_path?: string;
};

const authHeaders = (token: string) => ({
	Accept: 'application/json',
	'Content-Type': 'application/json',
	authorization: `Bearer ${token}`
});

const parseError = async (res: Response) => {
	try {
		const body = await res.json();
		return body?.detail || res.statusText;
	} catch {
		return res.statusText;
	}
};

export const getMapaStatus = async (token: string): Promise<MapaStatus | null> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/mapa/status`, {
		method: 'GET',
		headers: authHeaders(token)
	});
	if (!res.ok) throw await parseError(res);
	return res.json();
};

export const getMapaNombres = async (token: string): Promise<string[]> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/mapa/nombres`, {
		method: 'GET',
		headers: authHeaders(token)
	});
	if (!res.ok) throw await parseError(res);
	const data = await res.json();
	return data?.nombres ?? [];
};

export const getMapaGeojson = async (token: string): Promise<Record<string, unknown>> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/mapa/geojson`, {
		method: 'GET',
		headers: authHeaders(token)
	});
	if (!res.ok) throw await parseError(res);
	return res.json();
};

export const consultarMapaPunto = async (
	token: string,
	lat: number,
	lon: number
): Promise<MapaConsultaResult> => {
	const params = new URLSearchParams({ lat: String(lat), lon: String(lon) });
	const res = await fetch(`${WEBUI_API_BASE_URL}/mapa/consulta?${params}`, {
		method: 'GET',
		headers: authHeaders(token)
	});
	if (!res.ok) throw await parseError(res);
	return res.json();
};

export const buscarMapaNombre = async (token: string, q: string): Promise<MapaConsultaResult> => {
	const params = new URLSearchParams({ q });
	const res = await fetch(`${WEBUI_API_BASE_URL}/mapa/buscar?${params}`, {
		method: 'GET',
		headers: authHeaders(token)
	});
	if (!res.ok) throw await parseError(res);
	return res.json();
};

export const getMapaHighlight = async (
	token: string,
	nombre: string
): Promise<Record<string, unknown>> => {
	const params = new URLSearchParams({ nombre });
	const res = await fetch(`${WEBUI_API_BASE_URL}/mapa/highlight?${params}`, {
		method: 'GET',
		headers: authHeaders(token)
	});
	if (!res.ok) throw await parseError(res);
	return res.json();
};
