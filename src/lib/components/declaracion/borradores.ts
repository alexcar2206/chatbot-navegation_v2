/** localStorage drafts for the Declaración wizard (scoped per user). */

export const BORRADORES_KEY_LEGACY = 'minosil_dr_borradores';
export const BORRADORES_VERSION = 1;
export const MAX_BORRADORES = 10;

export type BorradorEntrada = {
	id: string;
	nombre: string;
	actualizado: string;
	dr_paso: number;
	dr_datos: Record<string, unknown>;
};

export type BorradoresAlmacen = {
	version: number;
	borradores: BorradorEntrada[];
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

export const leerBorradores = (userId: string): BorradorEntrada[] => {
	if (typeof localStorage === 'undefined' || !userId) return [];
	try {
		const raw = localStorage.getItem(claveBorradores(userId));
		if (!raw) return [];
		const data = JSON.parse(raw) as BorradoresAlmacen;
		if (data?.version !== BORRADORES_VERSION || !Array.isArray(data.borradores)) return [];
		return data.borradores.slice(0, MAX_BORRADORES);
	} catch {
		return [];
	}
};

export const escribirBorradores = (userId: string, lista: BorradorEntrada[]) => {
	if (typeof localStorage === 'undefined' || !userId) return;
	const payload: BorradoresAlmacen = {
		version: BORRADORES_VERSION,
		borradores: lista.slice(0, MAX_BORRADORES)
	};
	localStorage.setItem(claveBorradores(userId), JSON.stringify(payload));
};

/** Removes the pre-user-scoped shared drafts key (privacy). */
export const limpiarBorradoresCompartidos = () => {
	if (typeof localStorage === 'undefined') return;
	localStorage.removeItem(BORRADORES_KEY_LEGACY);
};

export const upsertBorrador = (
	lista: BorradorEntrada[],
	entrada: BorradorEntrada
): BorradorEntrada[] => {
	const idx = lista.findIndex((e) => e.id === entrada.id);
	if (idx >= 0) {
		const next = [...lista];
		next[idx] = entrada;
		return next;
	}
	if (lista.length >= MAX_BORRADORES) {
		throw new Error(`MAX_BORRADORES:${MAX_BORRADORES}`);
	}
	return [...lista, entrada];
};

export const eliminarBorrador = (lista: BorradorEntrada[], id: string): BorradorEntrada[] =>
	lista.filter((e) => e.id !== id);

export const nuevoId = (): string =>
	typeof crypto !== 'undefined' && crypto.randomUUID
		? crypto.randomUUID()
		: `dr-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
