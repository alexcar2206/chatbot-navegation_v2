/**
 * Drafts for the Declaración wizard.
 *
 * The server is the source of truth; localStorage (scoped per user) is a cache and an
 * offline queue: every change is written locally first and pushed in the background.
 */

import { derived, get, writable, type Readable } from 'svelte/store';
import {
	actualizarBorrador,
	ConflictoBorrador,
	crearBorrador,
	eliminarBorradorServidor,
	ErrorBorrador,
	ErrorRed,
	listarBorradores,
	obtenerBorrador,
	type BorradorServidor
} from '$lib/apis/declaracion';

export const BORRADORES_KEY_LEGACY = 'minosil_dr_borradores';
export const BORRADORES_VERSION = 2;
const BORRADORES_VERSION_LOCAL_ANTIGUA = 1;

export type BorradorEntrada = {
	id: string;
	nombre: string;
	actualizado: string;
	dr_paso: number;
	dr_datos: Record<string, unknown>;
};

export type EstadoSync = 'sincronizado' | 'pendiente' | 'conflicto' | 'sin-conexion';

type EntradaCache = BorradorEntrada & {
	sync: 'sincronizado' | 'pendiente' | 'conflicto';
	/** Server version this copy is based on; null until the server has it. */
	version_servidor: number | null;
	/** False when only the server summary is known (datos not downloaded yet). */
	datos_completos: boolean;
	/** Tombstone for deletions made while offline. */
	eliminado?: boolean;
	/** Server copy that caused a conflict. */
	servidor?: BorradorServidor;
	/** Server rejection that retrying will not fix (validation, limit…). */
	error?: string;
	error_codigo?: string | null;
	/** Local edit counter, to detect edits made while a request was in flight. */
	rev: number;
};

type BorradoresAlmacen = {
	version: number;
	borradores: EntradaCache[];
};

export type BorradorListado = BorradorEntrada & {
	sync: EstadoSync;
	error?: string;
	servidor?: BorradorEntrada;
};

export const claveBorradores = (userId: string) => `minosil_dr_borradores:${userId}`;

export const evaluarMostrarSi = (
	regla: { eq?: [string, unknown]; neq?: [string, unknown]; in?: [string, unknown[]] } | undefined,
	datos: Record<string, unknown>
): boolean => {
	if (!regla) return true;
	if (regla.eq) {
		const [clave, esperado] = regla.eq;
		return datos[clave] === esperado;
	}
	if (regla.neq) {
		const [clave, esperado] = regla.neq;
		return datos[clave] !== esperado;
	}
	if (regla.in) {
		const [clave, opciones] = regla.in;
		return (opciones || []).includes(datos[clave]);
	}
	return true;
};

export const nombreBorradorSugerido = (datos: Record<string, unknown>): string => {
	const nombre = datos?.declarante_nombre;
	if (typeof nombre === 'string' && nombre.trim()) return nombre.trim();
	return 'Borrador';
};

export const nuevoId = (): string =>
	typeof crypto !== 'undefined' && crypto.randomUUID
		? crypto.randomUUID()
		: `dr-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

/** Removes the pre-user-scoped shared drafts key (privacy). */
export const limpiarBorradoresCompartidos = () => {
	if (typeof localStorage === 'undefined') return;
	localStorage.removeItem(BORRADORES_KEY_LEGACY);
};

const isoDesdeNs = (ns: number) =>
	new Date(Math.floor(ns / 1e6)).toISOString().replace(/\.\d{3}Z$/, 'Z');
const ahoraIso = () => new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');

const entradaDesdeServidor = (s: BorradorServidor): BorradorEntrada => ({
	id: s.id,
	nombre: s.nombre,
	actualizado: isoDesdeNs(s.updated_at),
	dr_paso: s.paso,
	dr_datos: s.datos || {}
});

const aEntradaPublica = (e: EntradaCache): BorradorEntrada => ({
	id: e.id,
	nombre: e.nombre,
	actualizado: e.actualizado,
	dr_paso: e.dr_paso,
	dr_datos: structuredClone(e.dr_datos)
});

const REINTENTOS_MS = [2000, 5000, 15000, 60000];

/** The entry changed state and must go through the queue again. */
class Reintentar extends Error {}

/** Id of the draft the wizard is editing (autosave target). */
export const borradorActivoId = writable<string | null>(null);

const crearRepositorio = () => {
	let userId = '';
	let token = '';
	let entradas: EntradaCache[] = [];
	let intentoReintento = 0;
	let temporizador: ReturnType<typeof setTimeout> | null = null;
	let sincronizando: Promise<void> | null = null;
	let repetirSync = false;
	let escuchando = false;

	const entradasStore = writable<EntradaCache[]>([]);
	const offline = writable(false);

	const lista: Readable<BorradorListado[]> = derived([entradasStore, offline], ([$e, $offline]) =>
		$e
			.filter((e) => !e.eliminado)
			.sort((a, b) => b.actualizado.localeCompare(a.actualizado))
			.map((e) => ({
				...aEntradaPublica(e),
				sync: (e.sync === 'pendiente' && $offline ? 'sin-conexion' : e.sync) as EstadoSync,
				error: e.error,
				servidor: e.servidor ? entradaDesdeServidor(e.servidor) : undefined
			}))
	);

	const estadoGlobal: Readable<EstadoSync> = derived([entradasStore, offline], ([$e, $offline]) => {
		if ($e.some((e) => e.sync === 'conflicto')) return 'conflicto';
		if ($e.some((e) => e.sync === 'pendiente')) return $offline ? 'sin-conexion' : 'pendiente';
		return 'sincronizado';
	});

	const persistir = () => {
		entradasStore.set([...entradas]);
		if (typeof localStorage === 'undefined' || !userId) return;
		const payload: BorradoresAlmacen = { version: BORRADORES_VERSION, borradores: entradas };
		try {
			localStorage.setItem(claveBorradores(userId), JSON.stringify(payload));
		} catch {
			/* quota exceeded: the server copy is still the source of truth */
		}
	};

	const leerCache = (): { entradas: EntradaCache[]; migrados: number } => {
		if (typeof localStorage === 'undefined' || !userId) return { entradas: [], migrados: 0 };
		try {
			const raw = localStorage.getItem(claveBorradores(userId));
			if (!raw) return { entradas: [], migrados: 0 };
			const data = JSON.parse(raw);
			if (!Array.isArray(data?.borradores)) return { entradas: [], migrados: 0 };
			if (data.version === BORRADORES_VERSION) return { entradas: data.borradores, migrados: 0 };
			if (data.version === BORRADORES_VERSION_LOCAL_ANTIGUA) {
				const migradas = (data.borradores as BorradorEntrada[]).map(
					(b): EntradaCache => ({
						...b,
						sync: 'pendiente',
						version_servidor: null,
						datos_completos: true,
						rev: 1
					})
				);
				return { entradas: migradas, migrados: migradas.length };
			}
		} catch {
			/* corrupted cache: start from the server copy */
		}
		return { entradas: [], migrados: 0 };
	};

	const buscar = (id: string) => entradas.find((e) => e.id === id);

	const quitar = (id: string) => {
		entradas = entradas.filter((e) => e.id !== id);
	};

	const programarReintento = () => {
		if (temporizador || !userId) return;
		const espera = REINTENTOS_MS[Math.min(intentoReintento, REINTENTOS_MS.length - 1)];
		intentoReintento += 1;
		temporizador = setTimeout(() => {
			temporizador = null;
			sincronizar();
		}, espera);
	};

	const marcarConectado = () => {
		offline.set(false);
		intentoReintento = 0;
	};

	const payloadDe = (e: EntradaCache) => ({ nombre: e.nombre, paso: e.dr_paso, datos: e.dr_datos });

	const aplicarServidor = (e: EntradaCache, s: BorradorServidor) => {
		Object.assign(e, entradaDesdeServidor(s), {
			sync: 'sincronizado',
			version_servidor: s.version,
			datos_completos: true,
			servidor: undefined,
			error: undefined,
			error_codigo: undefined
		});
	};

	/** Pushes one entry. Throws ErrorRed to stop the queue; other errors are stored on the entry. */
	const subirEntrada = async (e: EntradaCache) => {
		const rev = e.rev;
		const tokenUsado = token;
		try {
			if (e.eliminado) {
				await eliminarBorradorServidor(tokenUsado, e.id);
				quitar(e.id);
				return;
			}

			let respuesta: BorradorServidor;
			if (e.version_servidor === null) {
				const creado = await crearBorrador(tokenUsado, e.id, payloadDe(e));
				if (!creado.existente) {
					respuesta = creado;
				} else if (creado.version === 1) {
					// Our earlier create landed but the response was lost.
					respuesta = await actualizarBorrador(tokenUsado, e.id, payloadDe(e), 1);
				} else {
					throw new ConflictoBorrador(creado);
				}
			} else {
				respuesta = await actualizarBorrador(tokenUsado, e.id, payloadDe(e), e.version_servidor);
			}

			e.version_servidor = respuesta.version;
			e.error = undefined;
			if (e.rev === rev) {
				e.sync = 'sincronizado';
				e.actualizado = isoDesdeNs(respuesta.updated_at);
			}
		} catch (err) {
			if (err instanceof ErrorRed) throw err;
			if (err instanceof ConflictoBorrador) {
				e.sync = 'conflicto';
				e.servidor = err.actual;
			} else if (err instanceof ErrorBorrador && err.status === 404 && !e.eliminado) {
				// Deleted on the server (expired or removed elsewhere) while we still have edits: recreate.
				e.version_servidor = null;
				e.rev += 1;
				throw new Reintentar();
			} else if (err instanceof ErrorBorrador && (err.status === 401 || err.status === 403)) {
				throw new ErrorRed(err.message);
			} else {
				e.error = err instanceof Error ? err.message : String(err);
				e.error_codigo = err instanceof ErrorBorrador ? err.codigo : null;
			}
		} finally {
			persistir();
		}
	};

	const ejecutarCola = async () => {
		do {
			repetirSync = false;
			const cola = entradas.filter((e) => (e.sync === 'pendiente' && !e.error) || e.eliminado);
			for (const e of cola) {
				try {
					await subirEntrada(e);
				} catch (err) {
					if (err instanceof ErrorRed) {
						offline.set(true);
						programarReintento();
						return;
					}
					repetirSync = true;
				}
			}
			marcarConectado();
		} while (repetirSync);
	};

	const sincronizar = (): Promise<void> => {
		if (!userId || !token) return Promise.resolve();
		if (sincronizando) {
			repetirSync = true;
			return sincronizando;
		}
		sincronizando = ejecutarCola().finally(() => {
			sincronizando = null;
		});
		return sincronizando;
	};

	const descargarCompletos = async (ids: string[]) => {
		for (const id of ids) {
			try {
				const s = await obtenerBorrador(token, id);
				const e = buscar(id);
				if (e && e.sync === 'sincronizado' && !e.eliminado) aplicarServidor(e, s);
			} catch (err) {
				if (err instanceof ErrorRed) return;
			}
		}
		persistir();
	};

	const reconciliar = async () => {
		const resumenes = await listarBorradores(token);
		const enServidor = new Map(resumenes.map((r) => [r.id, r]));
		const aDescargar: string[] = [];

		for (const r of resumenes) {
			const e = buscar(r.id);
			if (!e) {
				entradas.push({
					id: r.id,
					nombre: r.nombre,
					actualizado: isoDesdeNs(r.updated_at),
					dr_paso: r.paso,
					dr_datos: {},
					sync: 'sincronizado',
					version_servidor: r.version,
					datos_completos: false,
					rev: 0
				});
				aDescargar.push(r.id);
			} else if (e.sync === 'sincronizado' && (e.version_servidor ?? 0) < r.version) {
				aDescargar.push(r.id);
			} else if (e.sync === 'sincronizado' && !e.datos_completos) {
				aDescargar.push(r.id);
			}
		}

		for (const e of [...entradas]) {
			if (enServidor.has(e.id) || e.version_servidor === null) continue;
			if (e.eliminado || e.sync === 'sincronizado') {
				quitar(e.id);
			} else {
				Object.assign(e, { version_servidor: null, sync: 'pendiente', servidor: undefined });
			}
		}

		marcarConectado();
		persistir();
		await descargarCompletos(aDescargar);
	};

	const alVolverConexion = () => {
		if (temporizador) {
			clearTimeout(temporizador);
			temporizador = null;
		}
		intentoReintento = 0;
		sincronizar();
	};

	const alCambiarVisibilidad = () => {
		if (document.visibilityState === 'visible' && get(offline)) alVolverConexion();
	};

	const escuchar = (activar: boolean) => {
		if (typeof window === 'undefined' || activar === escuchando) return;
		escuchando = activar;
		const metodo = activar ? 'addEventListener' : 'removeEventListener';
		window[metodo]('online', alVolverConexion);
		document[metodo]('visibilitychange', alCambiarVisibilidad);
	};

	const reiniciar = () => {
		if (temporizador) clearTimeout(temporizador);
		temporizador = null;
		intentoReintento = 0;
		entradas = [];
		userId = '';
		token = '';
		escuchar(false);
		offline.set(false);
		entradasStore.set([]);
		borradorActivoId.set(null);
	};

	return {
		lista,
		estadoGlobal,

		/** Paints the local cache, then reconciles with the server. Returns how many legacy drafts were queued for upload. */
		async iniciar(nuevoUserId: string, nuevoToken: string): Promise<{ migrados: number }> {
			if (!nuevoUserId) return { migrados: 0 };
			token = nuevoToken;
			let migrados = 0;
			if (nuevoUserId !== userId) {
				reiniciar();
				token = nuevoToken;
				userId = nuevoUserId;
				const cache = leerCache();
				entradas = cache.entradas;
				migrados = cache.migrados;
				persistir();
			}
			escuchar(true);
			try {
				await reconciliar();
			} catch (err) {
				if (err instanceof ErrorRed) {
					offline.set(true);
					programarReintento();
				}
				return { migrados };
			}
			await sincronizar();
			return { migrados };
		},

		/** Saves locally and tries to push. Throws ErrorBorrador when the server rejects it. */
		async guardar(entrada: BorradorEntrada): Promise<void> {
			let e = buscar(entrada.id);
			if (!e) {
				e = {
					...entrada,
					sync: 'pendiente',
					version_servidor: null,
					datos_completos: true,
					rev: 0
				};
				entradas.push(e);
			}
			Object.assign(e, {
				nombre: entrada.nombre,
				dr_paso: entrada.dr_paso,
				dr_datos: structuredClone(entrada.dr_datos),
				actualizado: ahoraIso(),
				sync: e.sync === 'conflicto' ? 'conflicto' : 'pendiente',
				eliminado: false,
				error: undefined,
				error_codigo: undefined,
				rev: e.rev + 1
			});
			persistir();
			await sincronizar();

			const tras = buscar(entrada.id);
			if (tras?.error) {
				const { error: mensaje, error_codigo: codigo } = tras;
				if (tras.version_servidor === null) {
					quitar(entrada.id);
					persistir();
				}
				throw new ErrorBorrador(422, codigo ?? null, mensaje);
			}
		},

		async eliminar(id: string): Promise<void> {
			const e = buscar(id);
			if (!e) return;
			if (e.version_servidor === null) {
				quitar(id);
			} else {
				e.eliminado = true;
				e.rev += 1;
			}
			if (get(borradorActivoId) === id) borradorActivoId.set(null);
			persistir();
			await sincronizar();
		},

		async cargar(id: string): Promise<BorradorEntrada> {
			const e = buscar(id);
			if (!e) throw new Error('Draft not found');
			if (!e.datos_completos) {
				const s = await obtenerBorrador(token, id);
				aplicarServidor(e, s);
				persistir();
			}
			return aEntradaPublica(e);
		},

		async resolverConflicto(id: string, opcion: 'local' | 'servidor' | 'copia'): Promise<void> {
			const e = buscar(id);
			if (!e || e.sync !== 'conflicto' || !e.servidor) return;
			const servidor = e.servidor;

			if (opcion === 'local') {
				Object.assign(e, {
					sync: 'pendiente',
					version_servidor: servidor.version,
					servidor: undefined,
					rev: e.rev + 1
				});
			} else {
				if (opcion === 'copia') {
					entradas.push({
						...aEntradaPublica(e),
						id: nuevoId(),
						nombre: `${e.nombre} (2)`,
						actualizado: ahoraIso(),
						sync: 'pendiente',
						version_servidor: null,
						datos_completos: true,
						rev: 1
					});
				}
				aplicarServidor(e, servidor);
			}
			persistir();
			await sincronizar();
		},

		limpiarCache(id: string) {
			if (typeof localStorage !== 'undefined' && id) localStorage.removeItem(claveBorradores(id));
			if (id === userId) reiniciar();
		}
	};
};

export const borradoresRepo = crearRepositorio();
