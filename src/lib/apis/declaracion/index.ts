import { WEBUI_API_BASE_URL } from '$lib/constants';

export type DeclaracionStatus = {
	available: boolean;
	plantilla_path: string;
	editable_path: string;
	limitaciones_mvp: string;
	total_pasos: number;
	total_pasos_datos: number;
	paso_revision: number;
};

export type MostrarSi =
	| { eq: [string, unknown] }
	| { neq: [string, unknown] }
	| { in: [string, unknown[]] };

export type CampoSchema = {
	clave: string;
	etiqueta: string;
	tipo: 'texto' | 'select' | 'numero' | 'fecha' | 'multiselect' | 'checkbox' | string;
	obligatorio?: boolean;
	opciones?: string[];
	mostrar_si?: MostrarSi;
	ayuda?: string;
	valor_inicial?: unknown;
	minimo?: number;
	maximo?: number;
	permite_vacio?: boolean;
	inicial_hoy?: boolean;
};

export type PasoSchema = {
	indice: number;
	titulo: string;
	campos: CampoSchema[];
};

export type DeclaracionSchema = {
	pasos: PasoSchema[];
	paso_revision: { indice: number; titulo: string };
	limitaciones_mvp: string;
	total_pasos: number;
};

export type ValidacionResult = {
	ok: boolean;
	errores: string[];
	paso?: number;
};

const authHeaders = (token: string) => ({
	Accept: 'application/json',
	'Content-Type': 'application/json',
	authorization: `Bearer ${token}`
});

const parseError = async (res: Response) => {
	try {
		const body = await res.json();
		if (body?.detail?.errores) return body.detail.errores.join('\n');
		if (Array.isArray(body?.detail)) {
			return body.detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('\n');
		}
		return body?.detail || res.statusText;
	} catch {
		return res.statusText;
	}
};

export const getDeclaracionStatus = async (token: string): Promise<DeclaracionStatus> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/declaracion/status`, {
		method: 'GET',
		headers: authHeaders(token)
	});
	if (!res.ok) throw await parseError(res);
	return res.json();
};

export const getDeclaracionSchema = async (token: string): Promise<DeclaracionSchema> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/declaracion/schema`, {
		method: 'GET',
		headers: authHeaders(token)
	});
	if (!res.ok) throw await parseError(res);
	return res.json();
};

export const validarPasoDeclaracion = async (
	token: string,
	paso: number,
	datos: Record<string, unknown>
): Promise<ValidacionResult> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/declaracion/validar-paso`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify({ paso, datos })
	});
	if (!res.ok) throw await parseError(res);
	return res.json();
};

export const validarDeclaracion = async (
	token: string,
	datos: Record<string, unknown>
): Promise<ValidacionResult> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/declaracion/validar`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify({ datos })
	});
	if (!res.ok) throw await parseError(res);
	return res.json();
};

export const regenerarDeclaracion = async (token: string): Promise<Record<string, unknown>> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/declaracion/regenerar`, {
		method: 'POST',
		headers: authHeaders(token)
	});
	if (!res.ok) throw await parseError(res);
	return res.json();
};

const filenameFromDisposition = (header: string | null): string | null => {
	if (!header) return null;
	const m = /filename="?([^";]+)"?/i.exec(header);
	return m?.[1] ?? null;
};

export const generarDeclaracion = async (
	token: string,
	datos: Record<string, unknown>
): Promise<{ blob: Blob; filename: string }> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/declaracion/generar`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify({ datos })
	});
	if (!res.ok) throw await parseError(res);
	const blob = await res.blob();
	const filename =
		filenameFromDisposition(res.headers.get('Content-Disposition')) ||
		'Declaracion_responsable.docx';
	return { blob, filename };
};
