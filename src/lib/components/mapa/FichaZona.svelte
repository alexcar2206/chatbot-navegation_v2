<script lang="ts">
	import { getContext } from 'svelte';
	import type { MapaConsultaResult, MapaUsoEmbalse, ZonaEstado } from '$lib/apis/mapa';
	import { config, user } from '$lib/stores';
	import { featureNavegacionDisponible } from '$lib/utils/navegacion';
	import EstadoBadge from '$lib/components/navegacion/ui/EstadoBadge.svelte';
	import FichaBloque from './FichaBloque.svelte';
	import { ESTILO_ESTADO } from './estados';
	import { ICONOS_MAPA, formatearNombrePropio, formatearNumero } from './formato';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let resultado: MapaConsultaResult;
	export let yaSeleccionada = false;
	export let onDeclarar: (() => void) | null = null;
	export let onAnadir: (() => void) | null = null;
	/** Fill parent height and pin action buttons at the bottom. */
	export let pieFijo = true;

	$: estado = (resultado?.navegacion?.estado ?? null) as ZonaEstado | null;
	$: navegacion = resultado?.navegacion ?? null;
	$: embalse = resultado?.embalse ?? null;
	$: ubicacion = [
		embalse?.rio ? `${$i18n.t('River')} ${formatearNombrePropio(embalse.rio)}` : '',
		formatearNombrePropio(embalse?.municipio)
	]
		.filter(Boolean)
		.join(' · ');

	$: mostrarAcciones =
		resultado?.encontrado &&
		featureNavegacionDisponible($config, $user, 'declaracion') &&
		(onDeclarar || onAnadir);

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
</script>

<div
	class="card-brand text-sm border-l-4 {estado
		? ESTILO_ESTADO[estado].borde
		: 'border-l-brand-700'} {pieFijo
		? 'flex h-full min-h-0 flex-col overflow-hidden px-0 py-0'
		: 'space-y-4 px-4 py-4'}"
>
	<div
		class="{pieFijo
			? 'min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-4 space-y-4'
			: 'contents'}"
	>
		<div class="flex flex-wrap items-start justify-between gap-3">
			<div class="min-w-0">
				{#if resultado.encontrado && resultado.nombre}
					<h3 class="text-base font-semibold tracking-tight text-brand-900 dark:text-brand-50">
						{resultado.nombre}
					</h3>
					{#if ubicacion}
						<p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">{ubicacion}</p>
					{/if}
				{:else}
					<p class="font-medium text-brand-900 dark:text-brand-50">{resultado.mensaje}</p>
				{/if}
			</div>
			{#if estado}
				<EstadoBadge {estado} />
			{/if}
		</div>

		{#if resultado.encontrado}
			{#if estado === 'ponars'}
				<div
					class="flex items-start gap-2.5 rounded-xl border border-violet-200 bg-violet-50 px-3 py-2.5 text-violet-900 dark:border-violet-900/60 dark:bg-violet-950/30 dark:text-violet-100"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.75"
						stroke="currentColor"
						class="mt-0.5 size-5 shrink-0"
						aria-hidden="true"
					>
						<path stroke-linecap="round" stroke-linejoin="round" d={ICONOS_MAPA.ponars} />
					</svg>
					<p>
						{$i18n.t(
							'Navigation in this reservoir is governed by the Ribeira Sacra Navigation and Mooring Plan (PONARS). Check its specific rules before sailing.'
						)}
					</p>
				</div>
			{/if}

			{#if navegacion && (navegacion.condiciones || navegacion.restricciones || navegacion.plazo)}
				<div class="grid gap-3 grid-cols-[repeat(auto-fit,minmax(14rem,1fr))]">
					{#if navegacion.condiciones}
						<FichaBloque
							titulo={$i18n.t('Conditions')}
							icono={ICONOS_MAPA.condiciones}
							texto={navegacion.condiciones}
							tono={estado === 'prohibida' ? 'peligro' : 'neutro'}
						/>
					{/if}
					{#if navegacion.restricciones}
						<FichaBloque
							titulo={$i18n.t('Restrictions')}
							icono={ICONOS_MAPA.restricciones}
							texto={navegacion.restricciones}
							tono={estado === 'prohibida' ? 'peligro' : 'aviso'}
						/>
					{/if}
					{#if navegacion.plazo}
						<FichaBloque
							titulo={$i18n.t('Declaration validity')}
							icono={ICONOS_MAPA.vigencia}
							texto={navegacion.plazo}
						>
							{#if navegacion.plazo_anios}
								<p class="text-2xl font-semibold text-brand-800 dark:text-brand-100">
									{$i18n.t('{{count}} years', { count: navegacion.plazo_anios })}
								</p>
							{/if}
						</FichaBloque>
					{/if}
				</div>
			{/if}

			<details
				class="group rounded-xl border border-gray-200/80 dark:border-gray-800 [&_summary::-webkit-details-marker]:hidden"
			>
				<summary
					class="flex cursor-pointer select-none list-none items-center justify-between px-3 py-2 text-xs font-semibold uppercase tracking-wide text-gray-600 dark:text-gray-300"
				>
					{$i18n.t('Reservoir details')}
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="2"
						stroke="currentColor"
						class="size-4 transition-transform group-open:rotate-180"
						aria-hidden="true"
					>
						<path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
					</svg>
				</summary>
				<div class="space-y-3 px-3 pb-3">
					{#if embalse?.usos.length}
						<div class="flex flex-wrap items-center gap-1.5">
							<span class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Uses')}:</span>
							{#each embalse.usos as uso}
								<span
									class="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-800 dark:bg-brand-950/50 dark:text-brand-100"
								>
									{usoEtiqueta(uso)}
								</span>
							{/each}
						</div>
					{/if}
					<dl class="grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3">
						{#if embalse?.superficie_ha != null}
							<div>
								<dt class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Surface')}</dt>
								<dd class="font-medium">{formatearNumero(embalse.superficie_ha, $i18n.language)} ha</dd>
							</div>
						{/if}
						{#if embalse?.volumen_hm3 != null}
							<div>
								<dt class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Volume')}</dt>
								<dd class="font-medium">{formatearNumero(embalse.volumen_hm3, $i18n.language)} hm³</dd>
							</div>
						{/if}
						{#if embalse?.titular}
							<div>
								<dt class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Owner')}</dt>
								<dd class="font-medium">{formatearNombrePropio(embalse.titular)}</dd>
							</div>
						{/if}
						{#if embalse?.anio != null}
							<div>
								<dt class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Year')}</dt>
								<dd class="font-medium">{embalse.anio}</dd>
							</div>
						{/if}
						{#if resultado.lat != null && resultado.lon != null}
							<div>
								<dt class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Centroid')}</dt>
								<dd class="font-medium tabular-nums">
									{resultado.lat.toFixed(5)}, {resultado.lon.toFixed(5)}
								</dd>
							</div>
						{/if}
					</dl>
				</div>
			</details>

			{#if resultado.embalse_mvp}
				<p class="text-xs text-gray-600 dark:text-gray-300">
					<span class="text-gray-500 dark:text-gray-400">{$i18n.t('MVP reservoir')}:</span>
					{resultado.embalse_mvp}
				</p>
			{:else if resultado.en_lista_mvp === false}
				<p class="text-xs text-amber-700 dark:text-amber-300">
					{$i18n.t('Not in the MVP list (option A). For the declaration use “Other reservoirs”.')}
				</p>
			{/if}

			{#if mostrarAcciones && estado === 'prohibida'}
				<div
					class="flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-xs text-red-800 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-200"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.75"
						stroke="currentColor"
						class="size-4 shrink-0"
						aria-hidden="true"
					>
						<path stroke-linecap="round" stroke-linejoin="round" d={ICONOS_MAPA.prohibido} />
					</svg>
					<p>
						{$i18n.t(
							'Navigation is prohibited in this reservoir. You can continue, but the responsible declaration will not enable navigation here.'
						)}
					</p>
				</div>
			{/if}

			{#if mostrarAcciones && !pieFijo}
				<div class="flex flex-wrap gap-2">
					{#if resultado.embalse_mvp}
						{#if onDeclarar}
							<button type="button" class="btn-brand" on:click={onDeclarar}>
								{$i18n.t('Declare at this reservoir')}
							</button>
						{/if}
						{#if onAnadir}
							<button
								type="button"
								class="btn-secondary disabled:opacity-50"
								disabled={yaSeleccionada}
								on:click={onAnadir}
							>
								{$i18n.t('Add to selection')}
							</button>
						{/if}
					{:else if resultado.nombre && onAnadir}
						<button
							type="button"
							class="btn-secondary disabled:opacity-50"
							disabled={yaSeleccionada}
							on:click={onAnadir}
						>
							{$i18n.t('Add as other reservoirs')}
						</button>
					{/if}
				</div>
			{/if}
		{/if}
	</div>

	{#if mostrarAcciones && pieFijo}
		<div
			class="shrink-0 border-t border-brand-100/80 dark:border-brand-800 bg-white/95 dark:bg-gray-950/95 px-4 py-3 flex flex-wrap gap-2"
		>
			{#if resultado.embalse_mvp}
				{#if onDeclarar}
					<button type="button" class="btn-brand" on:click={onDeclarar}>
						{$i18n.t('Declare at this reservoir')}
					</button>
				{/if}
				{#if onAnadir}
					<button
						type="button"
						class="btn-secondary disabled:opacity-50"
						disabled={yaSeleccionada}
						on:click={onAnadir}
					>
						{$i18n.t('Add to selection')}
					</button>
				{/if}
			{:else if resultado.nombre && onAnadir}
				<button
					type="button"
					class="btn-secondary disabled:opacity-50"
					disabled={yaSeleccionada}
					on:click={onAnadir}
				>
					{$i18n.t('Add as other reservoirs')}
				</button>
			{/if}
		</div>
	{/if}
</div>
