<script lang="ts">
	import { getContext } from 'svelte';
	import type { ZonaEstado } from '$lib/apis/mapa';
	import { claveEtiquetaEstado, estiloDeEstado } from '$lib/components/mapa/estados';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let estado: ZonaEstado | null | undefined = null;
	export let size: 'sm' | 'md' = 'md';

	$: estilo = estiloDeEstado(estado);
	$: etiqueta = estado ? $i18n.t(claveEtiquetaEstado(estado)) : $i18n.t('No status data');
</script>

<span
	class="inline-flex items-center gap-1.5 shrink-0 font-medium rounded-lg border {estilo.badge} {size ===
	'sm'
		? 'text-[0.65rem] px-1.5 py-0.5'
		: 'text-xs px-2.5 py-1'}"
>
	<span class="size-2 rounded-full {estilo.punto}" aria-hidden="true" />
	{etiqueta}
</span>
