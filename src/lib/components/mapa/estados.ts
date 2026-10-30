import type { ZonaEstado } from '$lib/apis/mapa';

export type EstiloEstado = {
	trazo: string;
	relleno: string;
	badge: string;
	punto: string;
	borde: string;
};

export const ESTILO_SIN_DATOS: EstiloEstado = {
	trazo: '#6b7280',
	relleno: '#9ca3af',
	badge:
		'bg-gray-100 text-gray-800 dark:bg-gray-800/60 dark:text-gray-200 border-gray-200/80 dark:border-gray-700/50',
	punto: 'bg-gray-400',
	borde: 'border-l-gray-400'
};

export const ESTILO_ESTADO: Record<ZonaEstado, EstiloEstado> = {
	permitida: {
		trazo: '#047857',
		relleno: '#10b981',
		badge:
			'bg-emerald-100 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-200 border-emerald-200/80 dark:border-emerald-800/50',
		punto: 'bg-emerald-500',
		borde: 'border-l-emerald-500'
	},
	restringida: {
		trazo: '#b45309',
		relleno: '#f59e0b',
		badge:
			'bg-amber-100 text-amber-950 dark:bg-amber-950/50 dark:text-amber-100 border-amber-200/80 dark:border-amber-800/50',
		punto: 'bg-amber-500',
		borde: 'border-l-amber-500'
	},
	prohibida: {
		trazo: '#b91c1c',
		relleno: '#ef4444',
		badge:
			'bg-red-100 text-red-900 dark:bg-red-950/50 dark:text-red-200 border-red-200/80 dark:border-red-800/50',
		punto: 'bg-red-500',
		borde: 'border-l-red-500'
	},
	ponars: {
		trazo: '#6d28d9',
		relleno: '#8b5cf6',
		badge:
			'bg-violet-100 text-violet-900 dark:bg-violet-950/50 dark:text-violet-200 border-violet-200/80 dark:border-violet-800/50',
		punto: 'bg-violet-500',
		borde: 'border-l-violet-500'
	}
};

/** Highlight when the consulted zone has no known navigation state. */
export const RESALTADO_SIN_ESTADO = { trazo: '#c2410c', relleno: '#fb923c' };

export const ORDEN_ESTADO: ZonaEstado[] = ['permitida', 'restringida', 'ponars', 'prohibida'];

export const estiloDeEstado = (estado: ZonaEstado | null | undefined): EstiloEstado =>
	estado && estado in ESTILO_ESTADO ? ESTILO_ESTADO[estado] : ESTILO_SIN_DATOS;

export const estiloLeaflet = (
	estado: ZonaEstado | null | undefined,
	opts: { weight?: number; fillOpacity?: number } = {}
) => {
	const e = estiloDeEstado(estado);
	return {
		color: e.trazo,
		weight: opts.weight ?? 1,
		fillColor: e.relleno,
		fillOpacity: opts.fillOpacity ?? 0.3
	};
};

/** i18n key for a zone status label. */
export const claveEtiquetaEstado = (estado: ZonaEstado): string => {
	switch (estado) {
		case 'permitida':
			return 'Allowed navigation';
		case 'restringida':
			return 'Restricted navigation';
		case 'prohibida':
			return 'Prohibited navigation';
		case 'ponars':
			return 'Regulated by PONARS';
	}
};
