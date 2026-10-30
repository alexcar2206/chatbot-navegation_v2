<script lang="ts">
	import { getContext } from 'svelte';
	import MapaZonas from '$lib/components/mapa/MapaZonas.svelte';
	import PageShell from '$lib/components/navegacion/ui/PageShell.svelte';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;
</script>

<PageShell
	title={$i18n.t('Map')}
	subtitle={$i18n.t(
		'Consult the navigation zones of Annex 3 (Miño-Sil): search by name, click the map, coordinates, or your location.'
	)}
	fullBleed
>
	<MapaZonas token={localStorage.token} />
</PageShell>
