<script lang="ts">
	import { getContext } from 'svelte';
	import type { EstadoSync } from './borradores';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let estado: EstadoSync = 'sincronizado';

	const ESTILOS: Record<EstadoSync, { punto: string; texto: string }> = {
		sincronizado: { punto: 'bg-emerald-500', texto: 'text-emerald-800 dark:text-emerald-200' },
		pendiente: { punto: 'bg-sky-500 animate-pulse', texto: 'text-sky-800 dark:text-sky-200' },
		'sin-conexion': { punto: 'bg-amber-500', texto: 'text-amber-800 dark:text-amber-200' },
		conflicto: { punto: 'bg-red-500', texto: 'text-red-800 dark:text-red-200' }
	};

	const etiqueta = (e: EstadoSync) => {
		_lang;
		switch (e) {
			case 'sincronizado':
				return $i18n.t('Saved to your account');
			case 'pendiente':
				return $i18n.t('Syncing…');
			case 'sin-conexion':
				return $i18n.t('Offline, saved on this device');
			case 'conflicto':
				return $i18n.t('Conflict');
		}
	};
</script>

<span class="inline-flex items-center gap-1.5 text-xs {ESTILOS[estado].texto}" role="status">
	<span class="size-2 shrink-0 rounded-full {ESTILOS[estado].punto}" aria-hidden="true" />
	{etiqueta(estado)}
</span>
