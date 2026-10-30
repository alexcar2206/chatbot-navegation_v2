<script lang="ts">
	import { getContext } from 'svelte';
	import type { MapaConsultaResult } from '$lib/apis/mapa';
	import { ESTILO_ESTADO, claveEtiquetaEstado } from './estados';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let seleccionadas: MapaConsultaResult[] = [];
	/** Compact chip that opens the confirmation flow (does not navigate). */
	export let compact = false;
	/** Full list with confirm/cancel (mobile confirmation sheet). */
	export let confirmacion = false;
	export let onQuitar: (clave: string) => void = () => {};
	export let onLimpiar: () => void = () => {};
	export let onDeclarar: () => void = () => {};
	export let onCancelar: () => void = () => {};
	export let onAbrir: () => void = () => {};

	const claveZona = (res: MapaConsultaResult): string | null =>
		res.embalse_mvp || res.nombre || null;
</script>

{#if compact}
	<button
		type="button"
		class="inline-flex items-center gap-2 rounded-full bg-brand-700 text-white shadow-lg px-3 py-2 text-sm font-medium hover:bg-brand-800 dark:bg-brand-600 dark:hover:bg-brand-500"
		on:click={onAbrir}
	>
		<span class="tabular-nums">{seleccionadas.length}</span>
		<span class="truncate max-w-[10rem]">{$i18n.t('Selected zones')}</span>
	</button>
{:else}
	<div
		class="card-brand px-4 py-3 text-sm flex flex-col gap-3 border-l-4 border-l-accent-500 h-full min-h-0 {confirmacion
			? 'shadow-xl dark:!bg-gray-950 dark:!border-gray-800'
			: ''}"
	>
		<div class="flex items-center justify-between gap-2 shrink-0">
			<p class="font-medium">
				{#if confirmacion}
					{$i18n.t('Use these zones in the declaration form?')}
				{:else}
					{$i18n.t('Selected zones')} ({seleccionadas.length})
				{/if}
			</p>
			{#if seleccionadas.length}
				<button
					type="button"
					class="text-xs text-gray-500 hover:text-gray-800 dark:hover:text-gray-200 underline"
					on:click={onLimpiar}
				>
					{$i18n.t('Clear selection')}
				</button>
			{/if}
		</div>
		{#if confirmacion}
			<p class="text-xs text-gray-500 dark:text-gray-400 -mt-1">
				{$i18n.t('You can remove zones individually before confirming.')}
			</p>
		{/if}
		<ul class="space-y-2 overflow-y-auto flex-1 min-h-0 max-h-64">
			{#each seleccionadas as zona (claveZona(zona))}
				{@const clave = claveZona(zona) || ''}
				<li
					class="flex items-center justify-between gap-2 rounded-lg bg-gray-50 {confirmacion
						? 'dark:bg-gray-900'
						: 'dark:bg-gray-900/50'} px-3 py-2"
				>
					<div class="min-w-0">
						<p class="flex items-center gap-1.5 font-medium">
							{#if zona.navegacion?.estado}
								<span
									class="size-2 shrink-0 rounded-full {ESTILO_ESTADO[zona.navegacion.estado].punto}"
									title={$i18n.t(claveEtiquetaEstado(zona.navegacion.estado))}
								/>
							{/if}
							<span class="truncate">{zona.nombre || clave}</span>
						</p>
						{#if zona.embalse_mvp}
							<p class="text-xs text-gray-500">
								{$i18n.t('MVP reservoir')}: {zona.embalse_mvp}
							</p>
						{:else}
							<p class="text-xs text-amber-700 dark:text-amber-300">
								{$i18n.t('Use as other reservoirs')}
							</p>
						{/if}
					</div>
					<button
						type="button"
						class="shrink-0 rounded-lg px-2 py-1 text-xs text-gray-600 hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-800"
						on:click={() => onQuitar(clave)}
					>
						{$i18n.t('Remove')}
					</button>
				</li>
			{/each}
		</ul>
		{#if !seleccionadas.length}
			<p class="text-xs text-gray-500 dark:text-gray-400">
				{$i18n.t('No zones selected')}
			</p>
		{/if}
		<div class="pt-1 shrink-0 flex flex-wrap gap-2">
			{#if confirmacion}
				<button type="button" class="btn-secondary flex-1 min-w-[7rem]" on:click={onCancelar}>
					{$i18n.t('Cancel')}
				</button>
				<button
					type="button"
					class="btn-brand flex-1 min-w-[7rem] disabled:opacity-50"
					disabled={!seleccionadas.length}
					on:click={onDeclarar}
				>
					{$i18n.t('Confirm')}
				</button>
			{:else}
				<button
					type="button"
					class="w-full btn-brand disabled:opacity-50"
					disabled={!seleccionadas.length}
					on:click={onDeclarar}
				>
					{$i18n.t('Use in declaration form')}
				</button>
			{/if}
		</div>
	</div>
{/if}
