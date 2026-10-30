<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { toast } from 'svelte-sonner';
	import {
		buscarMapaNombre,
		consultarMapaPunto,
		getMapaGeojson,
		getMapaNombres,
		getMapaStatus,
		type MapaConsultaResult
	} from '$lib/apis/mapa';
	import { config, showSidebar, user } from '$lib/stores';
	import { featureNavegacionDisponible } from '$lib/utils/navegacion';
	import type { AlturaSheet } from '$lib/components/navegacion/ui/BottomSheet.svelte';
	import { ORDEN_ESTADO, estiloDeEstado, claveEtiquetaEstado } from './estados';
	import {
		contarPorEstado,
		filtrarZonas,
		filtrosAUrl,
		filtrosDesdeUrl,
		filtrosVacios,
		ordenarZonas,
		type FiltrosZonas,
		type OrigenCoords,
		type ZonaFeature
	} from './filtros';
	import BuscadorZonas from './BuscadorZonas.svelte';
	import MapaLeaflet from './MapaLeaflet.svelte';
	import PanelZonas from './PanelZonas.svelte';
	import SeleccionZonas from './SeleccionZonas.svelte';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let token = '';

	let loading = true;
	let errorMsg = '';
	let nombres: string[] = [];
	let geojson: { type?: string; features?: ZonaFeature[] } | null = null;
	let features: ZonaFeature[] = [];
	let filtros: FiltrosZonas = filtrosVacios();
	let resultado: MapaConsultaResult | null = null;
	let seleccionadas: MapaConsultaResult[] = [];
	let querying = false;
	let latInput = '';
	let lonInput = '';
	let origen: OrigenCoords | null = null;
	let movil = false;
	let panelAbierto = true;
	let tab: 'zonas' | 'ficha' = 'zonas';
	let alturaSheet: AlturaSheet = 'peek';
	let confirmarSeleccion = false;
	let mapaRef: MapaLeaflet;

	$: features = (geojson?.features ?? []) as ZonaFeature[];
	$: contadores = contarPorEstado(features);
	$: filtradas = ordenarZonas(
		filtrarZonas(features, filtros),
		filtros.orden,
		filtros.dir,
		origen
	);
	$: mostrarDeclaracion = featureNavegacionDisponible($config, $user, 'declaracion');
	$: yaSeleccionada = resultado ? estaSeleccionada(resultado) : false;

	const claveZona = (res: MapaConsultaResult): string | null =>
		res.embalse_mvp || res.nombre || null;

	const estaSeleccionada = (res: MapaConsultaResult): boolean => {
		const clave = claveZona(res);
		if (!clave) return false;
		return seleccionadas.some((z) => claveZona(z) === clave);
	};

	const syncUrl = (f: FiltrosZonas) => {
		const params = filtrosAUrl(f);
		const qs = params.toString();
		const path = $page.url.pathname;
		goto(qs ? `${path}?${qs}` : path, {
			replaceState: true,
			noScroll: true,
			keepFocus: true
		});
	};

	const onFiltros = (f: FiltrosZonas) => {
		filtros = f;
		syncUrl(f);
	};

	const applyAndShow = async (
		res: MapaConsultaResult,
		opts: { queryLat?: number; queryLon?: number; fit?: boolean } = {}
	) => {
		resultado = res;
		tab = res.encontrado ? 'ficha' : tab;
		if (movil && res.encontrado) alturaSheet = 'media';
		mapaRef?.applyResult(res, opts);
	};

	const runConsulta = async (lat: number, lon: number) => {
		if (!token || querying) return;
		querying = true;
		latInput = String(lat);
		lonInput = String(lon);
		origen = { lat, lon };
		try {
			const res = await consultarMapaPunto(token, lat, lon);
			await applyAndShow(res, { queryLat: lat, queryLon: lon, fit: true });
		} catch (err) {
			mapaRef?.placeMarker(lat, lon);
			toast.error(typeof err === 'string' ? err : $i18n.t('Failed to query map point'));
		} finally {
			querying = false;
		}
	};

	const onBuscarNombre = async (nombre: string) => {
		if (!nombre || !token) return;
		querying = true;
		try {
			const res = await buscarMapaNombre(token, nombre);
			await applyAndShow(res, { fit: true });
			if (res.lat != null) latInput = String(res.lat);
			if (res.lon != null) lonInput = String(res.lon);
		} catch (err) {
			toast.error(typeof err === 'string' ? err : $i18n.t('Failed to search'));
		} finally {
			querying = false;
		}
	};

	const onUsarUbicacion = () => {
		if (!navigator.geolocation) {
			toast.error($i18n.t('Geolocation is not available in this browser'));
			return;
		}
		navigator.geolocation.getCurrentPosition(
			(pos) => {
				runConsulta(pos.coords.latitude, pos.coords.longitude);
			},
			() => toast.error($i18n.t('Could not get your location')),
			{ enableHighAccuracy: true, timeout: 15000 }
		);
	};

	const anadirASeleccion = () => {
		if (!resultado?.encontrado) return;
		const clave = claveZona(resultado);
		if (!clave) return;
		if (estaSeleccionada(resultado)) {
			toast.info($i18n.t('Already in the selection'));
			return;
		}
		seleccionadas = [...seleccionadas, resultado];
		if (resultado.navegacion?.estado === 'prohibida') {
			toast.warning($i18n.t('Added to selection, but navigation is prohibited in this reservoir'));
		} else {
			toast.success($i18n.t('Added to selection'));
		}
	};

	const quitarDeSeleccion = (clave: string) => {
		seleccionadas = seleccionadas.filter((z) => claveZona(z) !== clave);
		if (!seleccionadas.length) confirmarSeleccion = false;
	};

	const limpiarSeleccion = () => {
		seleccionadas = [];
		confirmarSeleccion = false;
	};

	const irADeclaracionEmbalse = () => {
		if (!resultado?.embalse_mvp) return;
		goto(`/declaracion?embalse=${encodeURIComponent(resultado.embalse_mvp)}`);
	};

	const irADeclaracion = () => {
		if (!seleccionadas.length) return;
		confirmarSeleccion = false;
		const params = new URLSearchParams();
		const otrosNombres: string[] = [];
		for (const z of seleccionadas) {
			if (z.embalse_mvp) params.append('embalse', z.embalse_mvp);
			else if (z.nombre) otrosNombres.push(z.nombre);
		}
		if (otrosNombres.length) params.set('otros', otrosNombres.join(', '));
		goto(`/declaracion?${params.toString()}`);
	};

	const medirViewport = () => {
		movil = typeof window !== 'undefined' && window.matchMedia('(max-width: 767px)').matches;
		if (!movil && typeof window !== 'undefined') {
			const md = window.matchMedia('(min-width: 768px) and (max-width: 1023px)').matches;
			if (md && $showSidebar) panelAbierto = false;
		}
	};

	onMount(async () => {
		medirViewport();
		window.addEventListener('resize', medirViewport);
		filtros = filtrosDesdeUrl($page.url.searchParams);

		try {
			const status = await getMapaStatus(token);
			if (!status?.available) {
				errorMsg = $i18n.t(
					'The map is not available yet. Wait for the docs pack seed and geo_cache generation.'
				);
				loading = false;
				return;
			}

			const [listaNombres, gj] = await Promise.all([
				getMapaNombres(token),
				getMapaGeojson(token)
			]);
			nombres = listaNombres;
			geojson = gj;
		} catch (err) {
			errorMsg = typeof err === 'string' ? err : $i18n.t('Could not load the map');
		} finally {
			loading = false;
		}

		return () => window.removeEventListener('resize', medirViewport);
	});
</script>

{#if loading}
	<div class="flex h-full items-center justify-center text-sm text-gray-500 dark:text-gray-400">
		{$i18n.t('Loading map…')}
	</div>
{:else if errorMsg}
	<div class="p-4">
		<div
			class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-sm text-red-800 dark:text-red-200"
		>
			{errorMsg}
		</div>
	</div>
{:else}
	<div class="relative flex h-full w-full min-h-0 overflow-hidden" data-sidebar-no-gesture>
		{#if !movil}
			<PanelZonas
				movil={false}
				{nombres}
				{features}
				{filtradas}
				{contadores}
				{filtros}
				{resultado}
				{querying}
				bind:latInput
				bind:lonInput
				{origen}
				{yaSeleccionada}
				{mostrarDeclaracion}
				bind:panelAbierto
				bind:tab
				onFiltros={onFiltros}
				onBuscar={onBuscarNombre}
				onConsultar={(lat, lon) => runConsulta(lat, lon)}
				onUbicacion={onUsarUbicacion}
				onAjustar={() => mapaRef?.ajustarAVisibles()}
				onDeclarar={irADeclaracionEmbalse}
				onAnadir={anadirASeleccion}
			/>
		{/if}

		<div class="relative flex-1 min-w-0 min-h-0">
			{#if movil}
				<div class="absolute inset-x-3 top-3 z-20 space-y-2 pointer-events-none">
					<div class="pointer-events-auto">
						<BuscadorZonas
							{nombres}
							{querying}
							bind:latInput
							bind:lonInput
							flotante
							mostrarCoords={false}
							on:buscar={(e) => onBuscarNombre(e.detail)}
							on:abrirFiltros={() => {
								tab = 'zonas';
								alturaSheet = 'completa';
							}}
						/>
					</div>
				</div>

				<button
					type="button"
					class="absolute right-3 z-20 size-11 rounded-full btn-brand shadow-lg !px-0"
					style="bottom: calc(6.5rem + env(safe-area-inset-bottom, 0px));"
					on:click={onUsarUbicacion}
					aria-label={$i18n.t('Use my location')}
					disabled={querying}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.75"
						stroke="currentColor"
						class="size-5 mx-auto"
						aria-hidden="true"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm0 0v-4m0-10V3m9 9h-4M7 12H3"
						/>
					</svg>
				</button>

				{#if seleccionadas.length && mostrarDeclaracion && !confirmarSeleccion}
					<div
						class="absolute left-3 right-3 z-20 flex justify-center pointer-events-none"
						style="bottom: calc(6.25rem + env(safe-area-inset-bottom, 0px));"
					>
						<div class="pointer-events-auto">
							<SeleccionZonas
								{seleccionadas}
								compact
								onAbrir={() => (confirmarSeleccion = true)}
							/>
						</div>
					</div>
				{/if}
			{:else}
				{#if seleccionadas.length && mostrarDeclaracion}
					<div class="absolute top-3 right-3 z-20 w-[min(100%,20rem)] pointer-events-auto">
						<SeleccionZonas
							{seleccionadas}
							onQuitar={quitarDeSeleccion}
							onLimpiar={limpiarSeleccion}
							onDeclarar={irADeclaracion}
						/>
					</div>
				{/if}
				<div
					class="pointer-events-none absolute bottom-3 left-3 z-20 hidden md:flex flex-wrap gap-2 rounded-xl bg-white/90 dark:bg-gray-950/90 backdrop-blur border border-brand-100 dark:border-brand-800 px-2.5 py-1.5 text-[0.65rem] shadow"
					role="note"
					aria-label={$i18n.t('Zone status legend')}
				>
					{#each ORDEN_ESTADO as estado}
						{@const estilo = estiloDeEstado(estado)}
						<span class="inline-flex items-center gap-1 text-gray-600 dark:text-gray-300">
							<span class="size-2 rounded-full {estilo.punto}" aria-hidden="true" />
							{$i18n.t(claveEtiquetaEstado(estado))}
						</span>
					{/each}
				</div>
			{/if}

			<MapaLeaflet
				bind:this={mapaRef}
				{geojson}
				zonasVisibles={filtradas}
				zoomControlPosition={movil ? 'bottomright' : 'topleft'}
				className="absolute inset-0 h-full w-full"
				on:click={(e) => runConsulta(e.detail.lat, e.detail.lon)}
			/>
		</div>

		{#if movil}
			<PanelZonas
				movil
				{nombres}
				{features}
				{filtradas}
				{contadores}
				{filtros}
				{resultado}
				{querying}
				bind:latInput
				bind:lonInput
				{origen}
				{yaSeleccionada}
				{mostrarDeclaracion}
				bind:tab
				bind:alturaSheet
				onFiltros={onFiltros}
				onBuscar={onBuscarNombre}
				onConsultar={(lat, lon) => runConsulta(lat, lon)}
				onUbicacion={onUsarUbicacion}
				onAjustar={() => mapaRef?.ajustarAVisibles()}
				onDeclarar={irADeclaracionEmbalse}
				onAnadir={anadirASeleccion}
			/>

			{#if confirmarSeleccion && mostrarDeclaracion}
				<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
				<div
					class="absolute inset-0 z-40 flex items-end justify-center bg-black/40 p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]"
					role="presentation"
					on:click|self={() => (confirmarSeleccion = false)}
				>
					<div
						class="w-full max-w-md max-h-[min(70vh,28rem)] overflow-hidden"
						role="dialog"
						aria-modal="true"
						aria-label={$i18n.t('Selected zones')}
					>
						<SeleccionZonas
							{seleccionadas}
							confirmacion
							onQuitar={quitarDeSeleccion}
							onLimpiar={limpiarSeleccion}
							onDeclarar={irADeclaracion}
							onCancelar={() => (confirmarSeleccion = false)}
						/>
					</div>
				</div>
			{/if}
		{/if}
	</div>
{/if}
