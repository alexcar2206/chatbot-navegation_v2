<script lang="ts">
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	export let titulo: string;
	/** Atributo `d` de un icono SVG de 24x24 con trazo. */
	export let icono: string;
	export let texto: string | null = null;
	export let tono: 'neutro' | 'aviso' | 'peligro' = 'neutro';

	const LIMITE_CARACTERES = 220;

	let expandido = false;
	$: texto, (expandido = false);
	$: largo = (texto?.length ?? 0) > LIMITE_CARACTERES;

	const TONOS = {
		neutro: {
			caja: 'border-gray-200/80 bg-gray-50/70 dark:border-gray-800 dark:bg-gray-900/40',
			icono: 'text-brand-600 dark:text-brand-300'
		},
		aviso: {
			caja: 'border-amber-200/80 bg-amber-50/70 dark:border-amber-900/60 dark:bg-amber-950/30',
			icono: 'text-amber-600 dark:text-amber-300'
		},
		peligro: {
			caja: 'border-red-200/80 bg-red-50/70 dark:border-red-900/60 dark:bg-red-950/30',
			icono: 'text-red-600 dark:text-red-300'
		}
	};
</script>

<section class="flex flex-col gap-2 rounded-xl border p-3 {TONOS[tono].caja}">
	<h4
		class="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-600 dark:text-gray-300"
	>
		<svg
			xmlns="http://www.w3.org/2000/svg"
			fill="none"
			viewBox="0 0 24 24"
			stroke-width="1.75"
			stroke="currentColor"
			class="size-4 shrink-0 {TONOS[tono].icono}"
			aria-hidden="true"
		>
			<path stroke-linecap="round" stroke-linejoin="round" d={icono} />
		</svg>
		{titulo}
	</h4>
	<slot />
	{#if texto}
		<p
			class="whitespace-pre-line leading-relaxed text-gray-700 dark:text-gray-200 {largo && !expandido
				? 'line-clamp-4'
				: ''}"
		>
			{texto}
		</p>
		{#if largo}
			<button
				type="button"
				class="self-start text-xs font-medium text-brand-700 hover:underline dark:text-brand-300"
				on:click={() => (expandido = !expandido)}
			>
				{expandido ? $i18n.t('Show less') : $i18n.t('Show more')}
			</button>
		{/if}
	{/if}
</section>
