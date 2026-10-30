<script lang="ts">
	import { getContext } from 'svelte';
	import type { MapaUsoEmbalse, ZonaEstado } from '$lib/apis/mapa';
	import Chip from '$lib/components/navegacion/ui/Chip.svelte';
	import { ORDEN_ESTADO, claveEtiquetaEstado, estiloDeEstado } from './estados';
	import {
		contarFiltrosActivos,
		filtrosVacios,
		listarRios,
		type FiltrosZonas,
		type OrdenZonas,
		type ZonaFeature
	} from './filtros';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let filtros: FiltrosZonas = filtrosVacios();
	export let features: ZonaFeature[] = [];
	export let contadores: Record<string, number> = {};
	export let total = 0;
	export let visibles = 0;
	export let distanciaDisponible = false;
	export let onChange: (f: FiltrosZonas) => void = () => {};
	export let onAjustar: (() => void) | null = null;

	$: rios = listarRios(features);
	$: activos = contarFiltrosActivos(filtros);

	const toggleEstado = (estado: ZonaEstado) => {
		const next = new Set(filtros.estados);
		if (next.has(estado)) next.delete(estado);
		else next.add(estado);
		onChange({ ...filtros, estados: next });
	};

	const toggleUso = (uso: MapaUsoEmbalse) => {
		const next = new Set(filtros.usos);
		if (next.has(uso)) next.delete(uso);
		else next.add(uso);
		onChange({ ...filtros, usos: next });
	};

	const limpiar = () => onChange(filtrosVacios());

	const usoEtiqueta = (uso: MapaUsoEmbalse) => {
		_lang;
		switch (uso) {
			case 'hidroelectrico':
				return $i18n.t('Hydroelectric');
			case 'abastecimiento':
				return $i18n.t('Water supply');
			case 'riego':
				return $i18n.t('Irrigation');
		}
	};

	const ordenes: { id: OrdenZonas; label: string }[] = [
		{ id: 'nombre', label: 'Name' },
		{ id: 'estado', label: 'Status' },
		{ id: 'superficie', label: 'Surface' },
		{ id: 'volumen', label: 'Volume' },
		{ id: 'plazo', label: 'Declaration validity' },
		{ id: 'distancia', label: 'Distance' }
	];
</script>

<div class="space-y-3 text-sm">
	<div class="flex flex-wrap items-center justify-between gap-2">
		<p class="text-xs text-gray-500 dark:text-gray-400">
			{$i18n.t('{{visible}} of {{total}} zones', { visible: visibles, total })}
			{#if activos}
				· {$i18n.t('{{count}} active filters', { count: activos })}
			{/if}
		</p>
		<div class="flex gap-2">
			{#if onAjustar}
				<button type="button" class="btn-ghost !min-h-8 text-xs" on:click={onAjustar}>
					{$i18n.t('Fit to results')}
				</button>
			{/if}
			{#if activos}
				<button type="button" class="btn-ghost !min-h-8 text-xs" on:click={limpiar}>
					{$i18n.t('Clear filters')}
				</button>
			{/if}
		</div>
	</div>

	<div class="flex flex-wrap gap-1.5" role="group" aria-label={$i18n.t('Zone status legend')}>
		{#each ORDEN_ESTADO as estado}
			{@const estilo = estiloDeEstado(estado)}
			<Chip
				active={filtros.estados.has(estado)}
				count={contadores[estado] ?? 0}
				on:click={() => toggleEstado(estado)}
			>
				<span class="size-2 rounded-full {estilo.punto}" aria-hidden="true" />
				{$i18n.t(claveEtiquetaEstado(estado))}
			</Chip>
		{/each}
	</div>

	<label class="flex items-center gap-2 text-sm cursor-pointer form-brand">
		<input
			type="checkbox"
			class="rounded"
			checked={filtros.soloMvp}
			on:change={(e) => onChange({ ...filtros, soloMvp: e.currentTarget.checked })}
		/>
		<span>{$i18n.t('Only form reservoirs')}</span>
	</label>

	<div class="flex flex-wrap gap-1.5">
		{#each ['hidroelectrico', 'abastecimiento', 'riego'] as uso}
			<Chip
				active={filtros.usos.has(uso as MapaUsoEmbalse)}
				on:click={() => toggleUso(uso as MapaUsoEmbalse)}
			>
				{usoEtiqueta(uso as MapaUsoEmbalse)}
			</Chip>
		{/each}
	</div>

	<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
		<label class="flex flex-col gap-1 text-xs text-gray-500">
			{$i18n.t('River')}
			<select
				class="input-brand !min-h-9"
				value={filtros.rio}
				on:change={(e) => onChange({ ...filtros, rio: e.currentTarget.value })}
			>
				<option value="">{$i18n.t('All rivers')}</option>
				{#each rios as rio}
					<option value={rio}>{rio}</option>
				{/each}
			</select>
		</label>
		<label class="flex flex-col gap-1 text-xs text-gray-500">
			{$i18n.t('Sort by')}
			<select
				class="input-brand !min-h-9"
				value={filtros.orden}
				on:change={(e) =>
					onChange({ ...filtros, orden: e.currentTarget.value as OrdenZonas })}
			>
				{#each ordenes as o}
					{#if o.id !== 'distancia' || distanciaDisponible}
						<option value={o.id}>{$i18n.t(o.label)}</option>
					{/if}
				{/each}
			</select>
		</label>
	</div>
</div>
