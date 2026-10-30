import type { ZonaEstado } from '$lib/apis/mapa';
import type { MapaUsoEmbalse } from '$lib/apis/mapa';
import { ORDEN_ESTADO } from './estados';

export type OrdenZonas =
	| 'nombre'
	| 'estado'
	| 'superficie'
	| 'volumen'
	| 'plazo'
	| 'distancia';

export type FiltrosZonas = {
	q: string;
	estados: Set<ZonaEstado>;
	soloMvp: boolean;
	usos: Set<MapaUsoEmbalse>;
	rio: string;
	orden: OrdenZonas;
	dir: 'asc' | 'desc';
};

export type ZonaFeature = {
	type?: string;
	geometry?: unknown;
	properties?: Record<string, unknown> | null;
};

export type OrigenCoords = { lat: number; lon: number };

export const filtrosVacios = (): FiltrosZonas => ({
	q: '',
	estados: new Set(),
	soloMvp: false,
	usos: new Set(),
	rio: '',
	orden: 'nombre',
	dir: 'asc'
});

export const tieneFiltrosActivos = (f: FiltrosZonas): boolean =>
	Boolean(f.q.trim()) ||
	f.estados.size > 0 ||
	f.soloMvp ||
	f.usos.size > 0 ||
	Boolean(f.rio.trim()) ||
	f.orden !== 'nombre' ||
	f.dir !== 'asc';

export const contarFiltrosActivos = (f: FiltrosZonas): number => {
	let n = 0;
	if (f.q.trim()) n += 1;
	if (f.estados.size) n += 1;
	if (f.soloMvp) n += 1;
	if (f.usos.size) n += 1;
	if (f.rio.trim()) n += 1;
	return n;
};

const props = (f: ZonaFeature) => f.properties ?? {};

const texto = (v: unknown) => String(v ?? '').trim();

const normalizar = (v: unknown) =>
	texto(v)
		.normalize('NFD')
		.replace(/\p{M}/gu, '')
		.toLowerCase();

export const contarPorEstado = (features: ZonaFeature[]): Record<string, number> => {
	const out: Record<string, number> = {
		permitida: 0,
		restringida: 0,
		prohibida: 0,
		ponars: 0,
		sin_datos: 0
	};
	for (const f of features) {
		const e = props(f)._estado;
		if (typeof e === 'string' && e in out) out[e] += 1;
		else out.sin_datos += 1;
	}
	return out;
};

export const listarRios = (features: ZonaFeature[]): string[] => {
	const set = new Set<string>();
	for (const f of features) {
		const rio = texto(props(f)._rio);
		if (rio) set.add(rio);
	}
	return [...set].sort((a, b) => a.localeCompare(b, 'es'));
};

export const filtrarZonas = (features: ZonaFeature[], filtros: FiltrosZonas): ZonaFeature[] => {
	const q = normalizar(filtros.q);
	return features.filter((f) => {
		const p = props(f);
		if (filtros.estados.size) {
			const e = p._estado;
			if (typeof e !== 'string' || !filtros.estados.has(e as ZonaEstado)) return false;
		}
		if (filtros.soloMvp && !p._mvp) return false;
		if (filtros.usos.size) {
			const usos = Array.isArray(p._usos) ? (p._usos as string[]) : [];
			if (![...filtros.usos].some((u) => usos.includes(u))) return false;
		}
		if (filtros.rio.trim()) {
			if (normalizar(p._rio) !== normalizar(filtros.rio)) return false;
		}
		if (q) {
			const hay = [p._nombre, p._mvp, p._rio, p._municipio].map(normalizar).join(' ');
			if (!hay.includes(q)) return false;
		}
		return true;
	});
};

const rangoEstado = (estado: unknown): number => {
	if (typeof estado !== 'string') return ORDEN_ESTADO.length;
	const i = ORDEN_ESTADO.indexOf(estado as ZonaEstado);
	return i >= 0 ? i : ORDEN_ESTADO.length;
};

const num = (v: unknown): number => {
	const n = typeof v === 'number' ? v : Number(v);
	return Number.isFinite(n) ? n : Number.NEGATIVE_INFINITY;
};

/** Haversine distance in km. */
export const distanciaKm = (a: OrigenCoords, b: OrigenCoords): number => {
	const R = 6371;
	const toRad = (d: number) => (d * Math.PI) / 180;
	const dLat = toRad(b.lat - a.lat);
	const dLon = toRad(b.lon - a.lon);
	const lat1 = toRad(a.lat);
	const lat2 = toRad(b.lat);
	const h =
		Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
	return 2 * R * Math.asin(Math.sqrt(h));
};

const centroideDe = (f: ZonaFeature): OrigenCoords | null => {
	const c = props(f)._centroide;
	if (!Array.isArray(c) || c.length < 2) return null;
	const lat = Number(c[0]);
	const lon = Number(c[1]);
	if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
	return { lat, lon };
};

export const ordenarZonas = (
	features: ZonaFeature[],
	orden: OrdenZonas,
	dir: 'asc' | 'desc' = 'asc',
	origen?: OrigenCoords | null
): ZonaFeature[] => {
	const mul = dir === 'asc' ? 1 : -1;
	const copia = [...features];
	copia.sort((a, b) => {
		const pa = props(a);
		const pb = props(b);
		let cmp = 0;
		switch (orden) {
			case 'estado':
				cmp = rangoEstado(pa._estado) - rangoEstado(pb._estado);
				break;
			case 'superficie':
				cmp = num(pa._superficie_ha) - num(pb._superficie_ha);
				break;
			case 'volumen':
				cmp = num(pa._volumen_hm3) - num(pb._volumen_hm3);
				break;
			case 'plazo':
				cmp = num(pa._plazo_anios) - num(pb._plazo_anios);
				break;
			case 'distancia': {
				if (!origen) {
					cmp = texto(pa._nombre).localeCompare(texto(pb._nombre), 'es');
					break;
				}
				const ca = centroideDe(a);
				const cb = centroideDe(b);
				const da = ca ? distanciaKm(origen, ca) : Number.POSITIVE_INFINITY;
				const db = cb ? distanciaKm(origen, cb) : Number.POSITIVE_INFINITY;
				cmp = da - db;
				break;
			}
			case 'nombre':
			default:
				cmp = texto(pa._nombre).localeCompare(texto(pb._nombre), 'es');
		}
		if (cmp === 0) cmp = texto(pa._nombre).localeCompare(texto(pb._nombre), 'es');
		return cmp * mul;
	});
	return copia;
};

const ESTADOS_VALIDOS = new Set<string>(['permitida', 'restringida', 'prohibida', 'ponars']);
const USOS_VALIDOS = new Set<string>(['hidroelectrico', 'abastecimiento', 'riego']);
const ORDENES_VALIDOS = new Set<string>([
	'nombre',
	'estado',
	'superficie',
	'volumen',
	'plazo',
	'distancia'
]);

export const filtrosDesdeUrl = (params: URLSearchParams): FiltrosZonas => {
	const f = filtrosVacios();
	f.q = params.get('q') ?? '';
	const estados = (params.get('estado') ?? '')
		.split(',')
		.map((s) => s.trim())
		.filter((s) => ESTADOS_VALIDOS.has(s)) as ZonaEstado[];
	f.estados = new Set(estados);
	f.soloMvp = params.get('mvp') === '1';
	const usos = (params.get('uso') ?? '')
		.split(',')
		.map((s) => s.trim())
		.filter((s) => USOS_VALIDOS.has(s)) as MapaUsoEmbalse[];
	f.usos = new Set(usos);
	f.rio = params.get('rio') ?? '';
	const orden = params.get('orden') ?? 'nombre';
	if (ORDENES_VALIDOS.has(orden)) f.orden = orden as OrdenZonas;
	const dir = params.get('dir');
	if (dir === 'desc' || dir === 'asc') f.dir = dir;
	return f;
};

export const filtrosAUrl = (filtros: FiltrosZonas, base?: URLSearchParams): URLSearchParams => {
	const params = new URLSearchParams(base);
	for (const k of ['q', 'estado', 'mvp', 'uso', 'rio', 'orden', 'dir']) params.delete(k);
	if (filtros.q.trim()) params.set('q', filtros.q.trim());
	if (filtros.estados.size) params.set('estado', [...filtros.estados].join(','));
	if (filtros.soloMvp) params.set('mvp', '1');
	if (filtros.usos.size) params.set('uso', [...filtros.usos].join(','));
	if (filtros.rio.trim()) params.set('rio', filtros.rio.trim());
	if (filtros.orden !== 'nombre') params.set('orden', filtros.orden);
	if (filtros.dir !== 'asc') params.set('dir', filtros.dir);
	return params;
};
