<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { WEBUI_NAME, config, user } from '$lib/stores';
	import { featureNavegacionDisponible } from '$lib/utils/navegacion';
	import { goto } from '$app/navigation';

	const i18n = getContext('i18n');

	let loaded = false;

	onMount(async () => {
		if (!featureNavegacionDisponible($config, $user, 'mapa')) {
			goto('/');
			return;
		}
		loaded = true;
	});
</script>

<svelte:head>
	<title>
		{$i18n.t('Map')} / {$WEBUI_NAME}
	</title>
</svelte:head>

{#if loaded}
	<slot />
{/if}
