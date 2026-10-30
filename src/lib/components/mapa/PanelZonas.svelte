<script lang="ts">
	import { getContext, createEventDispatcher } from 'svelte';
	import type { MapaConsultaResult } from '$lib/apis/mapa';
	import BottomSheet, { type AlturaSheet } from '$lib/components/navegacion/ui/BottomSheet.svelte';
	import EstadoBadge from '$lib/components/navegacion/ui/EstadoBadge.svelte';
	import BuscadorZonas from './BuscadorZonas.svelte';
	import FichaZona from './FichaZona.svelte';
	import FiltrosZonas from './FiltrosZonas.svelte';
	import ListaZonas from './ListaZonas.svelte';
	import {
		contarFiltrosActivos,
		filtrosVacios,
		type FiltrosZonas as Filtros,
		type OrigenCoords,
		type ZonaFeature
	} from './filtros';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let movil = false;
	export let nombres: string[] = [];
	export let features: ZonaFeature[] = [];
	export let filtradas: ZonaFeature[] = [];
	export let contadores: Record<string, number> = {};
	export let filtros: Filtros = filtrosVacios();
	export let resultado: MapaConsultaResult | null = null;
	export let querying = false;
	export let latInput = '';
	export let lonInput = '';
	export let origen: OrigenCoords | null = null;
	export let yaSeleccionada = false;
	export let mostrarDeclaracion = false;
	export let panelAbierto = true;
	export let tab: 'zonas' | 'ficha' = 'zonas';
	export let alturaSheet: AlturaSheet = 'peek';

	export let onFiltros: (f: Filtros) => void = () => {};
	export let onBuscar: (nombre: string) => void = () => {};
	export let onConsultar: (lat: number, lon: number) => void = () => {};
	export let onUbicacion: () => void = () => {};
	export let onAjustar: () => void = () => {};
	export let onDeclarar: () => void = () => {};
	export let onAnadir: () => void = () => {};

	const dispatch = createEventDispatcher<{
		altura: AlturaSheet;
		tab: 'zonas' | 'ficha';
		togglePanel: boolean;
	}>();

	$: activos = contarFiltrosActivos(filtros);

	const peekTexto = () => {
		if (resultado?.encontrado && resultado.nombre) return resultado.nombre;
		return $i18n.t('{{visible}} of {{total}} zones', {
			visible: filtradas.length,
			total: features.length
		});
	};

	const irFicha = () => {
		tab = 'ficha';
		dispatch('tab', 'ficha');
		if (movil) {
			alturaSheet = 'media';
			dispatch('altura', 'media');
		}
	};
</script>

{#if movil}
	<BottomSheet
		bind:altura={alturaSheet}
		on:altura={(e) => dispatch('altura', e.detail)}
		aria-label={$i18n.t('Zones panel')}
	>
		<div slot="handle" class="flex items-center justify-between gap-2 pb-1">
			<div class="min-w-0 flex items-center gap-2">
				<p class="truncate text-sm font-semibold text-brand-900 dark:text-brand-50">
					{peekTexto()}
				</p>
				{#if resultado?.navegacion?.estado}
					<EstadoBadge estado={resultado.navegacion.estado} size="sm" />
				{:else if activos}
					<span class="text-xs text-gray-500">
						{$i18n.t('{{count}} active filters', { count: activos })}
					</span>
				{/if}
			</div>
		</div>

		<div class="flex shrink-0 gap-1 mb-3">
			<button
				type="button"
				class="chip flex-1 justify-center {tab === 'zonas' ? 'chip-active' : ''}"
				on:click={() => {
					tab = 'zonas';
					dispatch('tab', 'zonas');
				}}
			>
				{$i18n.t('Zones')}
			</button>
			<button
				type="button"
				class="chip flex-1 justify-center {tab === 'ficha' ? 'chip-active' : ''}"
				disabled={!resultado}
				on:click={irFicha}
			>
				{$i18n.t('Details')}
			</button>
		</div>

		{#if tab === 'zonas'}
			<div class="min-h-0 flex-1 overflow-y-auto overscroll-contain space-y-3">
				<FiltrosZonas
					{filtros}
					{features}
					{contadores}
					total={features.length}
					visibles={filtradas.length}
					distanciaDisponible={!!origen}
					onChange={onFiltros}
					onAjustar={onAjustar}
				/>
				<ListaZonas
					features={filtradas}
					orden={filtros.orden}
					{origen}
					onSeleccionar={onBuscar}
					onLimpiarFiltros={() => onFiltros(filtrosVacios())}
				/>
			</div>
		{:else if resultado}
			<div class="min-h-0 flex-1 overflow-hidden">
				<FichaZona
					{resultado}
					{yaSeleccionada}
					pieFijo
					onDeclarar={mostrarDeclaracion ? onDeclarar : null}
					onAnadir={mostrarDeclaracion ? onAnadir : null}
				/>
			</div>
		{/if}
	</BottomSheet>
{:else}
	<aside
		class="relative shrink-0 flex flex-col border-r border-brand-100 dark:border-brand-900 bg-white/90 dark:bg-gray-950/90 backdrop-blur transition-[width] duration-200 {panelAbierto
			? 'w-[min(100%,380px)]'
			: 'w-10'}"
	>
		<button
			type="button"
			class="absolute top-3 -right-3 z-10 size-7 rounded-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-xs shadow"
			on:click={() => {
				panelAbierto = !panelAbierto;
				dispatch('togglePanel', panelAbierto);
			}}
			aria-label={panelAbierto ? $i18n.t('Collapse panel') : $i18n.t('Expand panel')}
		>
			{panelAbierto ? '‹' : '›'}
		</button>

		{#if panelAbierto}
			<div class="flex flex-col gap-3 p-3 h-full min-h-0 overflow-hidden">
				<BuscadorZonas
					{nombres}
					{querying}
					bind:latInput
					bind:lonInput
					on:buscar={(e) => onBuscar(e.detail)}
					on:consultar={(e) => onConsultar(e.detail.lat, e.detail.lon)}
					on:ubicacion={onUbicacion}
				/>

				<div class="flex gap-1 shrink-0">
					<button
						type="button"
						class="chip flex-1 justify-center {tab === 'zonas' ? 'chip-active' : ''}"
						on:click={() => {
							tab = 'zonas';
							dispatch('tab', 'zonas');
						}}
					>
						{$i18n.t('Zones')}
					</button>
					<button
						type="button"
						class="chip flex-1 justify-center {tab === 'ficha' ? 'chip-active' : ''}"
						disabled={!resultado}
						on:click={irFicha}
					>
						{$i18n.t('Details')}
					</button>
				</div>

				<div class="flex-1 min-h-0 overflow-hidden flex flex-col">
					{#if tab === 'zonas'}
						<div class="min-h-0 flex-1 overflow-y-auto space-y-3">
							<FiltrosZonas
								{filtros}
								{features}
								{contadores}
								total={features.length}
								visibles={filtradas.length}
								distanciaDisponible={!!origen}
								onChange={onFiltros}
								onAjustar={onAjustar}
							/>
							<ListaZonas
								features={filtradas}
								orden={filtros.orden}
								{origen}
								onSeleccionar={onBuscar}
								onLimpiarFiltros={() => onFiltros(filtrosVacios())}
							/>
						</div>
					{:else if resultado}
						<div class="min-h-0 flex-1 overflow-hidden">
							<FichaZona
								{resultado}
								{yaSeleccionada}
								pieFijo
								onDeclarar={mostrarDeclaracion ? onDeclarar : null}
								onAnadir={mostrarDeclaracion ? onAnadir : null}
							/>
						</div>
					{/if}
				</div>
			</div>
		{/if}
	</aside>
{/if}
