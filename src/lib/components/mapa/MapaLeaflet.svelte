<script lang="ts">
	import { createEventDispatcher, onDestroy, onMount } from 'svelte';
	import type { MapaConsultaResult, ZonaEstado } from '$lib/apis/mapa';
	import { ESTILO_ESTADO, RESALTADO_SIN_ESTADO, estiloLeaflet } from './estados';
	import type { ZonaFeature } from './filtros';

	export let geojson: { type?: string; features?: ZonaFeature[] } | null = null;
	/** Features currently visible (filtered). When null, shows all of geojson. */
	export let zonasVisibles: ZonaFeature[] | null = null;
	export let zoomControlPosition: 'topleft' | 'topright' | 'bottomleft' | 'bottomright' =
		'topleft';
	export let className = 'h-full w-full';

	const dispatch = createEventDispatcher<{
		click: { lat: number; lon: number };
		ready: void;
	}>();

	const DEFAULT_CENTER: [number, number] = [42.4, -7.6];
	const DEFAULT_ZOOM = 8;
	const QUERY_ZOOM = 12;

	let mapElement: HTMLDivElement;
	let map: any = null;
	let L: any = null;
	let zonesLayer: any = null;
	let highlightLayer: any = null;
	let markerLayer: any = null;
	let resizeObs: ResizeObserver | null = null;
	let destroyed = false;
	let ready = false;

	const admiteTooltipHover = () =>
		typeof window !== 'undefined' && window.matchMedia('(hover: hover)').matches;

	const invalidate = () => {
		try {
			map?.invalidateSize();
		} catch {
			/* empty */
		}
	};

	const idsVisibles = (): Set<string> | null => {
		if (!zonasVisibles) return null;
		return new Set(
			zonasVisibles
				.map((f) => String(f?.properties?._nombre ?? ''))
				.filter(Boolean)
		);
	};

	const rebuildZones = () => {
		if (!map || !L || !geojson) return;
		if (zonesLayer) {
			map.removeLayer(zonesLayer);
			zonesLayer = null;
		}
		const visibles = idsVisibles();
		const conTooltip = admiteTooltipHover();
		zonesLayer = L.geoJSON(geojson, {
			filter: (feature: any) => {
				if (!visibles) return true;
				const nombre = feature?.properties?._nombre;
				return nombre != null && visibles.has(String(nombre));
			},
			style: (feature: any) =>
				estiloLeaflet(feature?.properties?._estado as ZonaEstado | null | undefined),
			onEachFeature: (feature: any, layer: any) => {
				const nombre = feature?.properties?._nombre;
				if (conTooltip && nombre) {
					layer.bindTooltip(String(nombre), { sticky: true, direction: 'top' });
				}
			}
		}).addTo(map);
	};

	export const ajustarAVisibles = () => {
		if (!map || !zonesLayer) return;
		try {
			const b = zonesLayer.getBounds();
			if (b?.isValid?.()) map.fitBounds(b, { padding: [20, 20] });
		} catch {
			/* empty */
		}
	};

	export const placeMarker = (lat: number, lon: number, label?: string | null) => {
		if (!map || !L) return;
		if (markerLayer) {
			map.removeLayer(markerLayer);
			markerLayer = null;
		}
		const popup = document.createElement('div');
		popup.textContent = label || `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
		markerLayer = L.marker([lat, lon]).bindPopup(popup).addTo(map);
	};

	export const clearHighlight = () => {
		if (highlightLayer && map) {
			map.removeLayer(highlightLayer);
			highlightLayer = null;
		}
	};

	export const applyResult = (
		res: MapaConsultaResult,
		opts: { queryLat?: number; queryLon?: number; fit?: boolean } = {}
	) => {
		const fit = opts.fit !== false;
		if (!map || !L) return;
		clearHighlight();

		const markerLat = opts.queryLat ?? res.lat;
		const markerLon = opts.queryLon ?? res.lon;
		if (
			markerLat != null &&
			markerLon != null &&
			Number.isFinite(markerLat) &&
			Number.isFinite(markerLon)
		) {
			placeMarker(markerLat, markerLon, res.nombre);
		}

		const features = (geojson?.features ?? []).filter(
			(f) => f?.properties?._nombre === res.nombre
		);
		if (res.encontrado && res.nombre && features.length) {
			const estadoRes = res.navegacion?.estado;
			const colores = estadoRes ? ESTILO_ESTADO[estadoRes] : RESALTADO_SIN_ESTADO;
			try {
				highlightLayer = L.geoJSON(
					{ type: 'FeatureCollection', features },
					{
						style: {
							color: colores.trazo,
							weight: 3,
							fillColor: colores.relleno,
							fillOpacity: 0.45
						}
					}
				).addTo(map);
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

	$: if (ready && geojson) rebuildZones();
	$: if (ready && zonasVisibles !== undefined) rebuildZones();

	onMount(async () => {
		const leafletMod = await import('leaflet');
		await import('leaflet/dist/leaflet.css');
		if (destroyed || !mapElement) return;
		L = leafletMod.default;

		map = L.map(mapElement, {
			zoomControl: false
		}).setView(DEFAULT_CENTER, DEFAULT_ZOOM);
		L.control.zoom({ position: zoomControlPosition }).addTo(map);
		L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution:
				'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
		}).addTo(map);

		map.on('click', (e: any) => {
			dispatch('click', { lat: e.latlng.lat, lon: e.latlng.lng });
		});

		resizeObs = new ResizeObserver(() => invalidate());
		resizeObs.observe(mapElement);

		ready = true;
		if (geojson) {
			rebuildZones();
			ajustarAVisibles();
		}
		dispatch('ready');
	});

	onDestroy(() => {
		destroyed = true;
		resizeObs?.disconnect();
		resizeObs = null;
		if (map) {
			map.remove();
			map = null;
		}
	});
</script>

<div bind:this={mapElement} class="z-10 bg-gray-100 dark:bg-gray-900 {className}" />
