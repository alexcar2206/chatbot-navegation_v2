<script lang="ts">
	import { getContext } from 'svelte';
	import { showSidebar } from '$lib/stores';
	import SidebarIcon from '$lib/components/icons/Sidebar.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	/** Page title shown in the header. */
	export let title = '';
	/** Optional subtitle under the title (desktop) or below the header. */
	export let subtitle = '';
	/** When true, content fills the viewport with no page scroll (map). */
	export let fullBleed = false;
	/** Extra classes for the content wrapper. */
	export let contentClass = '';
</script>

<div
	class="flex flex-col w-full max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
		? 'md:max-w-[calc(100%-var(--sidebar-width))]'
		: ''} max-w-full {fullBleed ? 'h-[100dvh] overflow-hidden' : 'h-screen'}"
>
	<header
		class="shrink-0 flex items-center gap-2 px-3 py-2.5 border-b border-brand-100/80 dark:border-brand-900/60 bg-gradient-to-r from-brand-50/80 via-white to-warm-50/60 dark:from-brand-950/80 dark:via-gray-950 dark:to-gray-950"
	>
		{#if !$showSidebar}
			<Tooltip content={$i18n.t('Open Sidebar')} placement="bottom">
				<button
					type="button"
					class="cursor-pointer flex size-8 items-center justify-center rounded-lg hover:bg-brand-100/70 dark:hover:bg-brand-900/50 transition"
					on:click={() => showSidebar.set(true)}
					aria-label={$i18n.t('Open Sidebar')}
				>
					<SidebarIcon className="size-4.5" strokeWidth="1.5" />
				</button>
			</Tooltip>
		{/if}
		<div class="min-w-0 flex-1">
			<h1 class="text-lg font-semibold tracking-tight text-brand-900 dark:text-brand-50 truncate">
				{title}
			</h1>
			{#if subtitle && !fullBleed}
				<p class="hidden sm:block text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
					{subtitle}
				</p>
			{/if}
		</div>
		{#if $$slots.acciones}
			<div class="flex items-center gap-2 shrink-0">
				<slot name="acciones" />
			</div>
		{/if}
	</header>

	{#if fullBleed}
		<div class="flex-1 min-h-0 relative {contentClass}">
			<slot />
		</div>
	{:else}
		<div class="flex-1 overflow-y-auto surface-page">
			<div class="px-3 sm:px-4 py-4 {contentClass}">
				{#if subtitle}
					<p class="sm:hidden text-sm text-gray-500 dark:text-gray-400 mb-3">{subtitle}</p>
				{/if}
				<slot />
			</div>
		</div>
	{/if}
</div>
