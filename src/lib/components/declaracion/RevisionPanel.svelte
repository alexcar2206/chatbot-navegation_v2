<script lang="ts">
	import { getContext } from 'svelte';
	import type { PasoSchema } from '$lib/apis/declaracion';
	import { evaluarMostrarSi } from './borradores';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let pasos: PasoSchema[] = [];
	export let datos: Record<string, unknown> = {};

	const fmt = (valor: unknown): string => {
		if (valor == null || valor === '') return '—';
		if (typeof valor === 'boolean') return valor ? $i18n.t('Yes') : $i18n.t('No');
		if (Array.isArray(valor)) return valor.length ? valor.join(', ') : '—';
		return String(valor);
	};
</script>

<div class="space-y-5">
	{#each pasos as paso}
		<section class="rounded-xl border border-gray-200 dark:border-gray-800 px-4 py-3 space-y-2">
			<h3 class="text-sm font-semibold">{paso.titulo}</h3>
			<dl class="space-y-1 text-sm">
				{#each paso.campos.filter((c) => evaluarMostrarSi(c.mostrar_si as any, datos)) as campo}
					<div class="flex flex-col sm:flex-row sm:gap-2">
						<dt class="text-gray-500 dark:text-gray-400 sm:min-w-[40%]">{campo.etiqueta}</dt>
						<dd class="text-gray-900 dark:text-gray-100 break-words">{fmt(datos[campo.clave])}</dd>
					</div>
				{/each}
			</dl>
		</section>
	{/each}
</div>
