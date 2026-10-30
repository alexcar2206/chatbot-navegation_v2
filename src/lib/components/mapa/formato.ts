const CONECTORES = new Set(['a', 'as', 'da', 'de', 'del', 'do', 'e', 'el', 'la', 'las', 'los', 'o', 'os', 'y']);

/** Title-case Annex 3 names; keep province codes like «(OR)» uppercase. */
export const formatearNombrePropio = (texto: string | null | undefined): string => {
	if (!texto) return '';
	return texto
		.split(' ')
		.map((palabra, i) => {
			if (palabra.startsWith('(')) return palabra.toUpperCase();
			const minus = palabra.toLocaleLowerCase('es');
			if (i > 0 && CONECTORES.has(minus)) return minus;
			return minus.replace(/(^|-)(\p{L})/gu, (_, sep, letra) => sep + letra.toLocaleUpperCase('es'));
		})
		.join(' ');
};

export const formatearNumero = (valor: number, locale = 'es') =>
	new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format(valor);

export const ICONOS_MAPA = {
	condiciones:
		'm11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z',
	restricciones:
		'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z',
	vigencia:
		'M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5',
	ponars:
		'M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0 0 12 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75Z',
	prohibido:
		'M18.364 18.364A9 9 0 0 0 5.636 5.636m12.728 12.728A9 9 0 0 1 5.636 5.636m12.728 12.728L5.636 5.636'
};
