<script lang="ts">
	import { getContext } from 'svelte';
	import type { ZonaEstado } from '$lib/apis/mapa';
	import { estiloDeEstado } from './estados';
	import { formatearNombrePropio, formatearNumero } from './formato';
	import { distanciaKm, type OrdenZonas, type OrigenCoords, type ZonaFeature } from './filtros';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let features: ZonaFeature[] = [];
	export let orden: OrdenZonas = 'nombre';
	export let origen: OrigenCoords | null = null;
	export let onSeleccionar: (nombre: string) => void = () => {};
	export let onLimpiarFiltros: (() => void) | null = null;

	const meta = (f: ZonaFeature) => {
		const p = f.properties ?? {};
		const rio = formatearNombrePropio(p._rio as string);
		const mun = formatearNombrePropio(p._municipio as string);
		const ubi = [rio, mun].filter(Boolean).join(' · ');
		let extra = '';
		if (orden === 'superficie' && p._superficie_ha != null) {
			extra = `${formatearNumero(Number(p._superficie_ha), $i18n.language)} ha`;
		} else if (orden === 'volumen' && p._volumen_hm3 != null) {
			extra = `${formatearNumero(Number(p._volumen_hm3), $i18n.language)} hm³`;
		} else if (orden === 'plazo' && p._plazo_anios != null) {
			extra = $i18n.t('{{count}} years', { count: Number(p._plazo_anios) });
		} else if (orden === 'distancia' && origen && Array.isArray(p._centroide)) {
			const c = p._centroide as number[];
			const km = distanciaKm(origen, { lat: Number(c[0]), lon: Number(c[1]) });
			extra = `${formatearNumero(km, $i18n.language)} km`;
		}
		return { ubi, extra };
	};
</script>

{#if !features.length}
	<div class="rounded-xl border border-dashed border-gray-200 dark:border-gray-800 px-4 py-8 text-center text-sm text-gray-500">
		<p>{$i18n.t('No zones match the current filters')}</p>
		{#if onLimpiarFiltros}
			<button type="button" class="btn-ghost mt-2 text-xs" on:click={onLimpiarFiltros}>
				{$i18n.t('Clear filters')}
			</button>
		{/if}
	</div>
{:else}
	<ul class="divide-y divide-gray-100 dark:divide-gray-850 rounded-xl border border-gray-100 dark:border-gray-850 overflow-hidden">
		{#each features as f (f.properties?._nombre)}
			{@const p = f.properties ?? {}}
			{@const estilo = estiloDeEstado(p._estado as ZonaEstado)}
			{@const m = meta(f)}
			<li>
				<button
					type="button"
					class="w-full flex items-start gap-2.5 px-3 py-2.5 text-left hover:bg-brand-50/60 dark:hover:bg-brand-950/40 transition"
					on:click={() => {
						const n = p._nombre;
						if (typeof n === 'string' && n) onSeleccionar(n);
					}}
				>
					<span class="mt-1.5 size-2.5 shrink-0 rounded-full {estilo.punto}" aria-hidden="true" />
					<span class="min-w-0 flex-1">
						<span class="block font-medium text-sm text-brand-900 dark:text-brand-50 truncate">
							{p._nombre}
						</span>
						{#if m.ubi}
							<span class="block text-xs text-gray-500 dark:text-gray-400 truncate">{m.ubi}</span>
						{/if}
					</span>
					{#if m.extra}
						<span class="shrink-0 text-xs tabular-nums text-gray-500">{m.extra}</span>
					{/if}
				</button>
			</li>
		{/each}
	</ul>
{/if}
