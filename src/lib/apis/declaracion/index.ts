import { WEBUI_API_BASE_URL } from '$lib/constants';

export type DeclaracionStatus = {
	available: boolean;
	/** Only returned to admins. */
	plantilla_path?: string;
	editable_path?: string;
	limitaciones_mvp: string;
	total_pasos: number;
	total_pasos_datos: number;
	paso_revision: number;
	/** Days without changes before a server draft is deleted (0 = never). */
	borradores_ttl_dias?: number;
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

/**
 * Validation error from the backend. `codigo` is the Spanish message template and
 * also the i18n key; `params` fill its {{placeholders}}; `mensaje` is pre-rendered.
 */
export type ErrorValidacion = {
	codigo: string;
	params: Record<string, string>;
	mensaje: string;
};

export type ValidacionResult = {
	ok: boolean;
	errores: ErrorValidacion[];
	paso?: number;
	/** Effective registration that will be printed (only from /validar). */
	matricula?: string;
};

/** Thrown when the backend rejects the data with structured validation errors (422). */
export class ErroresValidacion extends Error {
	errores: ErrorValidacion[];

	constructor(errores: ErrorValidacion[]) {
		super(errores.map((e) => e.mensaje).join('\n'));
		this.errores = errores;
	}
}

const authHeaders = (token: string) => ({
	Accept: 'application/json',
	'Content-Type': 'application/json',
	authorization: `Bearer ${token}`
});

const parseError = async (res: Response) => {
	try {
		const body = await res.json();
		if (Array.isArray(body?.detail?.errores)) return new ErroresValidacion(body.detail.errores);
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

// --- Borradores en servidor ---------------------------------------------------

export type BorradorResumen = {
	id: string;
	nombre: string;
	paso: number;
	version: number;
	/** Epoch in nanoseconds. */
	created_at: number;
	updated_at: number;
};

export type BorradorServidor = BorradorResumen & {
	user_id: string;
	datos: Record<string, unknown>;
};

export type BorradorPayload = {
	nombre: string;
	paso: number;
	datos: Record<string, unknown>;
};

/** The request never reached the server (offline, DNS, CORS…): keep it queued and retry. */
export class ErrorRed extends Error {}

/** 409 on update: someone else saved first. `actual` is the server copy. */
export class ConflictoBorrador extends Error {
	actual: BorradorServidor;

	constructor(actual: BorradorServidor, mensaje?: string) {
		super(mensaje || 'Draft conflict');
		this.actual = actual;
	}
}

/** Any other rejection (validation, limit, not found…). Retrying will not help. */
export class ErrorBorrador extends Error {
	status: number;
	codigo: string | null;

	constructor(status: number, codigo: string | null, mensaje: string) {
		super(mensaje);
		this.status = status;
		this.codigo = codigo;
	}
}

const BORRADORES_URL = `${WEBUI_API_BASE_URL}/declaracion/borradores`;

const peticionBorrador = async <T>(
	token: string,
	path: string,
	init: RequestInit = {}
): Promise<T> => {
	let res: Response;
	try {
		res = await fetch(`${BORRADORES_URL}${path}`, { ...init, headers: authHeaders(token) });
	} catch (e: any) {
		throw new ErrorRed(String(e?.message || e));
	}
	if (res.ok) return res.json();

	let detail: any = null;
	try {
		detail = (await res.json())?.detail;
	} catch {
		/* empty */
	}
	if (res.status === 409 && detail?.codigo === 'CONFLICTO_VERSION' && detail?.actual) {
		throw new ConflictoBorrador(detail.actual, detail.mensaje);
	}
	if (res.status >= 500 || res.status === 0) {
		throw new ErrorRed(`HTTP ${res.status}`);
	}
	const mensaje =
		(typeof detail === 'string' && detail) ||
		detail?.mensaje ||
		(Array.isArray(detail?.errores) && detail.errores.map((e: any) => e.mensaje).join('\n')) ||
		res.statusText;
	const codigo =
		detail?.codigo ?? (Array.isArray(detail?.errores) ? detail.errores[0]?.codigo : null);
	throw new ErrorBorrador(res.status, codigo ?? null, mensaje);
};

export const listarBorradores = (token: string) =>
	peticionBorrador<BorradorResumen[]>(token, '/', { method: 'GET' });

export const obtenerBorrador = (token: string, id: string) =>
	peticionBorrador<BorradorServidor>(token, `/${encodeURIComponent(id)}`, { method: 'GET' });

export const crearBorrador = (token: string, id: string, payload: BorradorPayload) =>
	peticionBorrador<BorradorServidor & { existente: boolean }>(token, '/', {
		method: 'POST',
		body: JSON.stringify({ id, ...payload })
	});

export const actualizarBorrador = (
	token: string,
	id: string,
	payload: BorradorPayload,
	version: number
) =>
	peticionBorrador<BorradorServidor>(token, `/${encodeURIComponent(id)}`, {
		method: 'PUT',
		body: JSON.stringify({ ...payload, version })
	});

export const eliminarBorradorServidor = (token: string, id: string) =>
	peticionBorrador<{ eliminado: boolean }>(token, `/${encodeURIComponent(id)}`, {
		method: 'DELETE'
	});
