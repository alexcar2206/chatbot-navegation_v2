<script lang="ts">
	import { getContext } from 'svelte';
	import { showSidebar } from '$lib/stores';
	import MapaZonas from '$lib/components/mapa/MapaZonas.svelte';
	import SidebarIcon from '$lib/components/icons/Sidebar.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	const i18n = getContext('i18n');
	// Re-evaluate $i18n.t(...) when the user changes language in Settings.
	$: _lang = $i18n.language;
</script>

<div
	class="flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
		? 'md:max-w-[calc(100%-var(--sidebar-width))]'
		: ''} max-w-full"
>
	<div class="flex items-center gap-2 px-3 py-2.5 border-b border-gray-50 dark:border-gray-850">
		{#if !$showSidebar}
			<Tooltip content={$i18n.t('Open Sidebar')} placement="bottom">
				<button
					type="button"
					class="cursor-pointer flex size-8 items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-gray-850 transition"
					on:click={() => showSidebar.set(true)}
					aria-label={$i18n.t('Open Sidebar')}
				>
					<SidebarIcon className="size-4.5" strokeWidth="1.5" />
				</button>
			</Tooltip>
		{/if}
		<div class="text-lg font-medium">{$i18n.t('Map')}</div>
	</div>

	<div class="flex-1 overflow-y-auto px-3 sm:px-4 py-4">
		<div class="max-w-6xl mx-auto w-full">
			<p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
				{$i18n.t(
					'Consult the navigation zones of Annex 3 (Miño-Sil): search by name, click the map, coordinates, or your location.'
				)}
			</p>
			<MapaZonas token={localStorage.token} />
		</div>
	</div>
</div>
