import type { ErrorValidacion } from '$lib/apis/declaracion';

type Translate = (key: string, params?: Record<string, unknown>) => string;

/**
 * Backend schema texts and error templates are Spanish (the official form's
 * language) and double as i18n keys: untranslated locales fall back to Spanish.
 */
export const traducirError = (t: Translate, error: ErrorValidacion): string => {
	const params: Record<string, unknown> = { ...(error.params ?? {}) };
	if (typeof params.campo === 'string') params.campo = t(params.campo);
	return t(error.codigo, params);
};
