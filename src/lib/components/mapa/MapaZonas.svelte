<script lang="ts">
	import { getContext, onDestroy, onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import {
		buscarMapaNombre,
		consultarMapaPunto,
		getMapaGeojson,
		getMapaHighlight,
		getMapaNombres,
		getMapaStatus,
		type MapaConsultaResult
	} from '$lib/apis/mapa';
	import { config } from '$lib/stores';

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

	let loading = true;
	let errorMsg = '';
	let nombres: string[] = [];
	let selectedNombre = '';
	let latInput = '';
	let lonInput = '';
	let resultado: MapaConsultaResult | null = null;
	let querying = false;

	const DEFAULT_CENTER: [number, number] = [42.4, -7.6];
	const DEFAULT_ZOOM = 8;
	const QUERY_ZOOM = 12;

	const irADeclaracion = (opts: { embalse?: string; otros?: string }) => {
		const params = new URLSearchParams();
		if (opts.embalse) params.set('embalse', opts.embalse);
		if (opts.otros) params.set('otros', opts.otros);
		goto(`/declaracion?${params.toString()}`);
	};

	const placeMarker = (lat: number, lon: number, label?: string | null) => {
		if (!map || !L) return;
		if (markerLayer) {
			map.removeLayer(markerLayer);
			markerLayer = null;
		}
		markerLayer = L.marker([lat, lon])
			.bindPopup(label || `${lat.toFixed(5)}, ${lon.toFixed(5)}`)
			.addTo(map);
	};

	const clearHighlight = () => {
		if (highlightLayer && map) {
			map.removeLayer(highlightLayer);
			highlightLayer = null;
		}
	};

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

		if (res.encontrado && res.nombre) {
			try {
				const highlight = await getMapaHighlight(token, res.nombre);
				highlightLayer = L.geoJSON(highlight, {
					style: {
						color: '#c2410c',
						weight: 3,
						fillColor: '#fb923c',
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
		const lat = Number(latInput);
		const lon = Number(lonInput);
		if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
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
			if (!status?.available) {
				errorMsg = $i18n.t(
					'The map is not available yet. Wait for the docs pack seed and geo_cache generation.'
				);
				loading = false;
				return;
			}

			nombres = await getMapaNombres(token);
			const geojson = await getMapaGeojson(token);

			const leafletMod = await import('leaflet');
			await import('leaflet/dist/leaflet.css');
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

	<div class="z-10 w-full rounded-xl overflow-hidden border border-gray-200 dark:border-gray-800">
		<div bind:this={mapElement} class="h-[min(60vh,560px)] w-full z-10 bg-gray-100 dark:bg-gray-900" />
	</div>

	{#if resultado}
		<div
			class="rounded-xl border border-gray-200 dark:border-gray-800 px-4 py-3 text-sm space-y-2"
		>
			<p class="font-medium">{resultado.mensaje}</p>
			{#if resultado.encontrado}
				<dl class="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1 text-gray-600 dark:text-gray-300">
					{#if resultado.nombre}
						<div>
							<dt class="inline text-gray-500">{$i18n.t('Zone')}:</dt>
							<dd class="inline">{resultado.nombre}</dd>
						</div>
					{/if}
					{#if resultado.embalse_mvp}
						<div>
							<dt class="inline text-gray-500">{$i18n.t('MVP reservoir')}:</dt>
							<dd class="inline">{resultado.embalse_mvp}</dd>
						</div>
					{:else if resultado.en_lista_mvp === false}
						<div class="sm:col-span-2 text-amber-700 dark:text-amber-300">
							{$i18n.t(
								'Not in the MVP list (option A). For the declaration use “Other reservoirs”.'
							)}
						</div>
					{/if}
					{#if resultado.lat != null && resultado.lon != null}
						<div>
							<dt class="inline text-gray-500">{$i18n.t('Centroid')}:</dt>
							<dd class="inline">{resultado.lat.toFixed(5)}, {resultado.lon.toFixed(5)}</dd>
						</div>
					{/if}
				</dl>
				{#if $config?.features?.enable_declaracion ?? false}
					<div class="pt-2 flex flex-wrap gap-2">
						{#if resultado.embalse_mvp}
							<button
								type="button"
								class="rounded-xl bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900 px-3 py-1.5 text-sm font-medium"
								on:click={() => irADeclaracion({ embalse: resultado?.embalse_mvp || undefined })}
							>
								{$i18n.t('Use in declaration form')}
							</button>
						{:else if resultado.nombre}
							<button
								type="button"
								class="rounded-xl border border-gray-200 dark:border-gray-700 px-3 py-1.5 text-sm"
								on:click={() => irADeclaracion({ otros: resultado?.nombre || undefined })}
							>
								{$i18n.t('Use as other reservoirs')}
							</button>
						{/if}
					</div>
				{/if}
			{/if}
		</div>
	{/if}
</div>
