<script lang="ts">
	import { getContext } from 'svelte';
	import { showSidebar } from '$lib/stores';
	import DeclaracionWizard from '$lib/components/declaracion/DeclaracionWizard.svelte';
	import SidebarIcon from '$lib/components/icons/Sidebar.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	const i18n = getContext('i18n');
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
		<div class="text-lg font-medium">{$i18n.t('Declaration')}</div>
	</div>

	<div class="flex-1 overflow-y-auto px-3 sm:px-4 py-4">
		<div class="max-w-3xl mx-auto w-full">
			<p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
				{$i18n.t(
					'Fill in the responsible navigation declaration (Miño-Sil MVP) and download the official DOCX.'
				)}
			</p>
			<DeclaracionWizard token={localStorage.token} />
		</div>
	</div>
</div>
