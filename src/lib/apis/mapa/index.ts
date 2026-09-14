import { WEBUI_API_BASE_URL } from '$lib/constants';

export type MapaConsultaResult = {
	encontrado: boolean;
	nombre: string | null;
	embalse_mvp: string | null;
	en_lista_mvp: boolean;
	atributos: Record<string, unknown>;
	mensaje: string;
	bounds: [number, number, number, number] | null;
	indice: number | null;
	lat: number | null;
	lon: number | null;
};

export type MapaStatus = {
	available: boolean;
	cache_path: string;
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
