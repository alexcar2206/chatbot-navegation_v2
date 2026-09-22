<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { WEBUI_NAME, config } from '$lib/stores';
	import { goto } from '$app/navigation';

	const i18n = getContext('i18n');

	let loaded = false;

	onMount(async () => {
		if (!($config?.features?.enable_declaracion ?? false)) {
			goto('/');
			return;
		}
		loaded = true;
	});
</script>

<svelte:head>
	<title>
		{$i18n.t('Declaration')} / {$WEBUI_NAME}
	</title>
</svelte:head>

{#if loaded}
	<slot />
{/if}
