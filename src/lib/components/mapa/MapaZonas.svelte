<script lang="ts">
	import { getContext, onDestroy, onMount, tick } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import {
		buscarMapaNombre,
		consultarMapaPunto,
		getMapaGeojson,
		getMapaNombres,
		getMapaStatus,
		type MapaConsultaResult,
		type MapaUsoEmbalse,
		type ZonaEstado
	} from '$lib/apis/mapa';
	import { config, user } from '$lib/stores';
	import { featureNavegacionDisponible } from '$lib/utils/navegacion';
	import FichaBloque from './FichaBloque.svelte';

	const i18n = getContext('i18n');
	// Re-evaluate $i18n.t(...) when the user changes language in Settings.
	$: _lang = $i18n.language;

	export let token = '';

	let mapElement: HTMLDivElement;
	let map: any = null;
	let L: any = null;
	let zonesLayer: any = null;
	let highlightLayer: any = null;
	let markerLayer: any = null;
	let zonasGeojson: any = null;
	let destroyed = false;

	let loading = true;
	let errorMsg = '';
	let nombres: string[] = [];
	let selectedNombre = '';
	let latInput = '';
	let lonInput = '';
	let resultado: MapaConsultaResult | null = null;
	let seleccionadas: MapaConsultaResult[] = [];
	let querying = false;

	const DEFAULT_CENTER: [number, number] = [42.4, -7.6];
	const DEFAULT_ZOOM = 8;
	const QUERY_ZOOM = 12;

	// Leaflet needs a resize when the side list appears/disappears and changes map width.
	$: if (map && seleccionadas) {
		tick().then(() => {
			try {
				map?.invalidateSize();
			} catch {
				/* empty */
			}
		});
	}

	const ESTILO_ESTADO: Record<
		ZonaEstado,
		{ trazo: string; relleno: string; badge: string; punto: string; borde: string }
	> = {
		permitida: {
			trazo: '#047857',
			relleno: '#10b981',
			badge:
				'bg-emerald-100 text-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-200 border-emerald-200/80 dark:border-emerald-800/50',
			punto: 'bg-emerald-500',
			borde: 'border-l-emerald-500'
		},
		restringida: {
			trazo: '#b45309',
			relleno: '#f59e0b',
			badge:
				'bg-amber-100 text-amber-950 dark:bg-amber-950/50 dark:text-amber-100 border-amber-200/80 dark:border-amber-800/50',
			punto: 'bg-amber-500',
			borde: 'border-l-amber-500'
		},
		prohibida: {
			trazo: '#b91c1c',
			relleno: '#ef4444',
			badge:
				'bg-red-100 text-red-900 dark:bg-red-950/50 dark:text-red-200 border-red-200/80 dark:border-red-800/50',
			punto: 'bg-red-500',
			borde: 'border-l-red-500'
		},
		ponars: {
			trazo: '#6d28d9',
			relleno: '#8b5cf6',
			badge:
				'bg-violet-100 text-violet-900 dark:bg-violet-950/50 dark:text-violet-200 border-violet-200/80 dark:border-violet-800/50',
			punto: 'bg-violet-500',
			borde: 'border-l-violet-500'
		}
	};
	const RESALTADO_SIN_ESTADO = { trazo: '#c2410c', relleno: '#fb923c' };

	const ICONOS = {
		condiciones:
			'm11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z',
		restricciones:
			'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z',
		vigencia:
			'M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5',
		ponars:
			'M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0 0 12 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75Z',
		prohibido:
			'M18.364 18.364A9 9 0 0 0 5.636 5.636m12.728 12.728A9 9 0 0 1 5.636 5.636m12.728 12.728L5.636 5.636'
	};

	const estadoEtiqueta = (estado: ZonaEstado) => {
		_lang;
		switch (estado) {
			case 'permitida':
				return $i18n.t('Allowed navigation');
			case 'restringida':
				return $i18n.t('Restricted navigation');
			case 'prohibida':
				return $i18n.t('Prohibited navigation');
			case 'ponars':
				return $i18n.t('Regulated by PONARS');
		}
	};

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

	const CONECTORES = new Set(['a', 'as', 'da', 'de', 'del', 'do', 'e', 'el', 'la', 'las', 'los', 'o', 'os', 'y']);

	// El Anexo 3 trae ríos, municipios y titulares en mayúsculas; los códigos de provincia «(OR)» se conservan.
	const formatearNombrePropio = (texto: string | null | undefined): string => {
		if (!texto) return '';
		return texto
			.split(' ')
			.map((palabra, i) => {
				if (palabra.startsWith('(')) return palabra.toUpperCase();
				const minus = palabra.toLocaleLowerCase('es');
				if (i > 0 && CONECTORES.has(minus)) return minus;
				return minus.replace(/(^|-)(\p{L})/gu, (_, sep, letra) => sep + letra.toLocaleUpperCase('es'));
			})
			.join(' ');
	};

	const formatearNumero = (valor: number) =>
		new Intl.NumberFormat($i18n.language, { maximumFractionDigits: 2 }).format(valor);

	$: estado = resultado?.navegacion?.estado ?? null;
	$: navegacion = resultado?.navegacion ?? null;
	$: embalse = resultado?.embalse ?? null;
	$: ubicacion = [
		embalse?.rio ? `${$i18n.t('River')} ${formatearNombrePropio(embalse.rio)}` : '',
		formatearNombrePropio(embalse?.municipio)
	]
		.filter(Boolean)
		.join(' · ');

	const claveZona = (res: MapaConsultaResult): string | null =>
		res.embalse_mvp || res.nombre || null;

	const yaSeleccionada = (res: MapaConsultaResult): boolean => {
		const clave = claveZona(res);
		if (!clave) return false;
		return seleccionadas.some((z) => claveZona(z) === clave);
	};

	const anadirASeleccion = () => {
		if (!resultado?.encontrado) return;
		const clave = claveZona(resultado);
		if (!clave) return;
		if (yaSeleccionada(resultado)) {
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
	};

	const limpiarSeleccion = () => {
		seleccionadas = [];
	};

	const irADeclaracionEmbalse = () => {
		if (!resultado?.embalse_mvp) return;
		goto(`/declaracion?embalse=${encodeURIComponent(resultado.embalse_mvp)}`);
	};

	const irADeclaracion = () => {
		if (!seleccionadas.length) return;
		const params = new URLSearchParams();
		const otrosNombres: string[] = [];
		for (const z of seleccionadas) {
			if (z.embalse_mvp) {
				params.append('embalse', z.embalse_mvp);
			} else if (z.nombre) {
				otrosNombres.push(z.nombre);
			}
		}
		if (otrosNombres.length) {
			params.set('otros', otrosNombres.join(', '));
		}
		goto(`/declaracion?${params.toString()}`);
	};

	const placeMarker = (lat: number, lon: number, label?: string | null) => {
		if (!map || !L) return;
		if (markerLayer) {
			map.removeLayer(markerLayer);
			markerLayer = null;
		}
		const popup = document.createElement('div');
		popup.textContent = label || `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
		markerLayer = L.marker([lat, lon]).bindPopup(popup).addTo(map);
	};

	const clearHighlight = () => {
		if (highlightLayer && map) {
			map.removeLayer(highlightLayer);
			highlightLayer = null;
		}
	};

	const highlightFor = (nombre: string) => ({
		type: 'FeatureCollection',
		features: (zonasGeojson?.features ?? []).filter(
			(f: any) => f?.properties?._nombre === nombre
		)
	});

	const applyResult = async (
		res: MapaConsultaResult,
		opts: { queryLat?: number; queryLon?: number; fit?: boolean } = {}
	) => {
		const fit = opts.fit !== false;
		resultado = res;
		if (!map || !L) return;

		clearHighlight();

		const markerLat = opts.queryLat ?? res.lat;
		const markerLon = opts.queryLon ?? res.lon;

		if (markerLat != null && markerLon != null && Number.isFinite(markerLat) && Number.isFinite(markerLon)) {
			placeMarker(markerLat, markerLon, res.nombre);
		}

		const highlight = res.encontrado && res.nombre ? highlightFor(res.nombre) : null;
		if (highlight?.features.length) {
			const estadoRes = res.navegacion?.estado;
			const colores = estadoRes ? ESTILO_ESTADO[estadoRes] : RESALTADO_SIN_ESTADO;
			try {
				highlightLayer = L.geoJSON(highlight, {
					style: {
						color: colores.trazo,
						weight: 3,
						fillColor: colores.relleno,
						fillOpacity: 0.45
					}
				}).addTo(map);
				if (fit) {
					try {
						map.fitBounds(highlightLayer.getBounds(), { maxZoom: QUERY_ZOOM, padding: [24, 24] });
					} catch {
						if (markerLat != null && markerLon != null) {
							map.setView([markerLat, markerLon], QUERY_ZOOM);
						}
					}
				}
			} catch {
				if (fit && markerLat != null && markerLon != null) {
					map.setView([markerLat, markerLon], QUERY_ZOOM);
				}
			}
		} else if (fit && markerLat != null && markerLon != null) {
			map.setView([markerLat, markerLon], QUERY_ZOOM);
		}
	};

	const runConsulta = async (lat: number, lon: number) => {
		if (!token || querying) return;
		querying = true;
		latInput = String(lat);
		lonInput = String(lon);
		try {
			const res = await consultarMapaPunto(token, lat, lon);
			await applyResult(res, { queryLat: lat, queryLon: lon, fit: true });
		} catch (err) {
			placeMarker(lat, lon);
			if (map) map.setView([lat, lon], QUERY_ZOOM);
			toast.error(typeof err === 'string' ? err : $i18n.t('Failed to query map point'));
		} finally {
			querying = false;
		}
	};

	const onBuscarNombre = async () => {
		if (!selectedNombre || !token) return;
		querying = true;
		try {
			const res = await buscarMapaNombre(token, selectedNombre);
			await applyResult(res, { fit: true });
			if (res.lat != null) latInput = String(res.lat);
			if (res.lon != null) lonInput = String(res.lon);
		} catch (err) {
			toast.error(typeof err === 'string' ? err : $i18n.t('Failed to search'));
		} finally {
			querying = false;
		}
	};

	const onConsultarCoords = async () => {
		const latTxt = String(latInput ?? '').trim();
		const lonTxt = String(lonInput ?? '').trim();
		const lat = Number(latTxt);
		const lon = Number(lonTxt);
		if (!latTxt || !lonTxt || !Number.isFinite(lat) || !Number.isFinite(lon)) {
			toast.error($i18n.t('Enter valid latitude and longitude (EPSG:4326)'));
			return;
		}
		await runConsulta(lat, lon);
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

	onMount(async () => {
		try {
			const status = await getMapaStatus(token);
			if (destroyed) return;
			if (!status?.available) {
				errorMsg = $i18n.t(
					'The map is not available yet. Wait for the docs pack seed and geo_cache generation.'
				);
				loading = false;
				return;
			}

			const [listaNombres, geojson] = await Promise.all([
				getMapaNombres(token),
				getMapaGeojson(token)
			]);
			if (destroyed) return;
			nombres = listaNombres;
			zonasGeojson = geojson;

			const leafletMod = await import('leaflet');
			await import('leaflet/dist/leaflet.css');
			if (destroyed || !mapElement) return;
			L = leafletMod.default;

			map = L.map(mapElement).setView(DEFAULT_CENTER, DEFAULT_ZOOM);
			L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
				attribution:
					'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
			}).addTo(map);

			zonesLayer = L.geoJSON(geojson, {
				style: {
					color: '#1d4ed8',
					weight: 1,
					fillColor: '#3b82f6',
					fillOpacity: 0.2
				}
			}).addTo(map);

			try {
				map.fitBounds(zonesLayer.getBounds(), { padding: [20, 20] });
			} catch {
				/* empty */
			}

			map.on('click', (e: any) => {
				runConsulta(e.latlng.lat, e.latlng.lng);
			});
		} catch (err) {
			errorMsg = typeof err === 'string' ? err : $i18n.t('Could not load the map');
		} finally {
			loading = false;
		}
	});

	onDestroy(() => {
		destroyed = true;
		if (map) {
			map.remove();
			map = null;
		}
	});
</script>

<div class="flex flex-col gap-4 w-full">
	{#if loading}
		<div class="text-sm text-gray-500 dark:text-gray-400 py-8 text-center">
			{$i18n.t('Loading map…')}
		</div>
	{:else if errorMsg}
		<div
			class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-sm text-red-800 dark:text-red-200"
		>
			{errorMsg}
		</div>
	{:else}
		<div class="flex flex-col lg:flex-row gap-3">
			<div class="flex flex-1 flex-col sm:flex-row gap-2">
				<select
					class="flex-1 rounded-xl border border-gray-200 dark:border-gray-700 bg-transparent px-3 py-2 text-sm"
					bind:value={selectedNombre}
					aria-label={$i18n.t('Reservoir or zone')}
				>
					<option value="">{$i18n.t('Search reservoir / zone…')}</option>
					{#each nombres as nombre}
						<option value={nombre}>{nombre}</option>
					{/each}
				</select>
				<button
					type="button"
					class="rounded-xl px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 disabled:opacity-50"
					disabled={!selectedNombre || querying}
					on:click={onBuscarNombre}
				>
					{$i18n.t('Search')}
				</button>
			</div>

			<div class="flex flex-wrap items-end gap-2">
				<label class="flex flex-col gap-1 text-xs text-gray-500">
					{$i18n.t('Lat')}
					<input
						class="w-28 rounded-xl border border-gray-200 dark:border-gray-700 bg-transparent px-2 py-2 text-sm"
						bind:value={latInput}
						inputmode="decimal"
					/>
				</label>
				<label class="flex flex-col gap-1 text-xs text-gray-500">
					{$i18n.t('Lon')}
					<input
						class="w-28 rounded-xl border border-gray-200 dark:border-gray-700 bg-transparent px-2 py-2 text-sm"
						bind:value={lonInput}
						inputmode="decimal"
					/>
				</label>
				<button
					type="button"
					class="rounded-xl px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 disabled:opacity-50"
					disabled={querying}
					on:click={onConsultarCoords}
				>
					{$i18n.t('Consult point')}
				</button>
				<button
					type="button"
					class="rounded-xl px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 disabled:opacity-50"
					disabled={querying}
					on:click={onUsarUbicacion}
				>
					{$i18n.t('Use my location')}
				</button>
			</div>
		</div>

		<div class="text-xs text-gray-500 dark:text-gray-400">
			{$i18n.t('Click the map to query a zone. Coordinates use EPSG:4326.')}
		</div>
	{/if}

	<div class="flex flex-col lg:flex-row gap-3 w-full items-stretch">
		{#if seleccionadas.length > 0 && featureNavegacionDisponible($config, $user, 'declaracion')}
			<div
				class="order-1 lg:order-2 w-full lg:w-64 shrink-0 card-brand px-4 py-3 text-sm flex flex-col gap-3 lg:h-[min(60vh,560px)] border-l-4 border-l-accent-500"
			>
				<div class="flex items-center justify-between gap-2 shrink-0">
					<p class="font-medium">
						{$i18n.t('Selected zones')} ({seleccionadas.length})
					</p>
					<button
						type="button"
						class="text-xs text-gray-500 hover:text-gray-800 dark:hover:text-gray-200 underline"
						on:click={limpiarSeleccion}
					>
						{$i18n.t('Clear selection')}
					</button>
				</div>
				<ul class="space-y-2 overflow-y-auto flex-1 min-h-0">
					{#each seleccionadas as zona (claveZona(zona))}
						{@const clave = claveZona(zona) || ''}
						<li
							class="flex items-center justify-between gap-2 rounded-lg bg-gray-50 dark:bg-gray-900/50 px-3 py-2"
						>
							<div class="min-w-0">
								<p class="flex items-center gap-1.5 font-medium">
									{#if zona.navegacion?.estado}
										<span
											class="size-2 shrink-0 rounded-full {ESTILO_ESTADO[zona.navegacion.estado].punto}"
											title={estadoEtiqueta(zona.navegacion.estado)}
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
								on:click={() => quitarDeSeleccion(clave)}
							>
								{$i18n.t('Remove')}
							</button>
						</li>
					{/each}
				</ul>
				<div class="pt-1 shrink-0">
					<button
						type="button"
						class="w-full rounded-xl btn-brand px-3 py-1.5 text-sm font-medium"
						on:click={irADeclaracion}
					>
						{$i18n.t('Use in declaration form')}
					</button>
				</div>
			</div>
		{/if}

		<div
			class="order-2 lg:order-1 z-10 flex-1 min-w-0 rounded-xl overflow-hidden border border-gray-200 dark:border-gray-800"
		>
			<div
				bind:this={mapElement}
				class="h-[min(60vh,560px)] w-full z-10 bg-gray-100 dark:bg-gray-900"
			/>
		</div>
	</div>

	{#if resultado}
		<div
			class="card-brand px-4 py-4 text-sm space-y-4 border-l-4 {estado
				? ESTILO_ESTADO[estado].borde
				: 'border-l-brand-700'}"
		>
			<div class="flex flex-wrap items-start justify-between gap-3">
				<div class="min-w-0">
					{#if resultado.encontrado && resultado.nombre}
						<h3 class="text-base font-semibold text-brand-900 dark:text-brand-50">
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
					<span
						class="inline-flex items-center gap-1.5 shrink-0 text-xs font-medium px-2.5 py-1 rounded-lg border {ESTILO_ESTADO[
							estado
						].badge}"
					>
						<span class="size-2 rounded-full {ESTILO_ESTADO[estado].punto}" aria-hidden="true" />
						{estadoEtiqueta(estado)}
					</span>
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
							<path stroke-linecap="round" stroke-linejoin="round" d={ICONOS.ponars} />
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
								icono={ICONOS.condiciones}
								texto={navegacion.condiciones}
								tono={estado === 'prohibida' ? 'peligro' : 'neutro'}
							/>
						{/if}
						{#if navegacion.restricciones}
							<FichaBloque
								titulo={$i18n.t('Restrictions')}
								icono={ICONOS.restricciones}
								texto={navegacion.restricciones}
								tono={estado === 'prohibida' ? 'peligro' : 'aviso'}
							/>
						{/if}
						{#if navegacion.plazo}
							<FichaBloque
								titulo={$i18n.t('Declaration validity')}
								icono={ICONOS.vigencia}
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
									<dd class="font-medium">{formatearNumero(embalse.superficie_ha)} ha</dd>
								</div>
							{/if}
							{#if embalse?.volumen_hm3 != null}
								<div>
									<dt class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t('Volume')}</dt>
									<dd class="font-medium">{formatearNumero(embalse.volumen_hm3)} hm³</dd>
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

				{#if featureNavegacionDisponible($config, $user, 'declaracion')}
					{#if estado === 'prohibida'}
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
								<path stroke-linecap="round" stroke-linejoin="round" d={ICONOS.prohibido} />
							</svg>
							<p>
								{$i18n.t(
									'Navigation is prohibited in this reservoir. You can continue, but the responsible declaration will not enable navigation here.'
								)}
							</p>
						</div>
					{/if}
					<div class="flex flex-wrap gap-2">
						{#if resultado.embalse_mvp}
							<button
								type="button"
								class="rounded-xl btn-brand px-3 py-1.5 text-sm font-medium"
								on:click={irADeclaracionEmbalse}
							>
								{$i18n.t('Declare at this reservoir')}
							</button>
							<button
								type="button"
								class="rounded-xl border border-brand-200 dark:border-brand-700 text-brand-800 dark:text-brand-100 px-3 py-1.5 text-sm font-medium disabled:opacity-50 hover:bg-brand-50 dark:hover:bg-brand-950/50"
								disabled={yaSeleccionada(resultado)}
								on:click={anadirASeleccion}
							>
								{$i18n.t('Add to selection')}
							</button>
						{:else if resultado.nombre}
							<button
								type="button"
								class="rounded-xl border border-gray-200 dark:border-gray-700 px-3 py-1.5 text-sm disabled:opacity-50"
								disabled={yaSeleccionada(resultado)}
								on:click={anadirASeleccion}
							>
								{$i18n.t('Add as other reservoirs')}
							</button>
						{/if}
					</div>
				{/if}
			{/if}
		</div>
	{/if}
</div>
