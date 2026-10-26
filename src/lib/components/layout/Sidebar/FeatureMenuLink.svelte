<script lang="ts">
	import { createEventDispatcher, getContext, tick } from 'svelte';
	import { goto } from '$app/navigation';

	import { mobile, showSidebar } from '$lib/stores';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import PinIcon from './icons/Pin.svelte';
	import PinSlashIcon from './icons/PinSlash.svelte';

	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let href: string;
	export let label: string;
	export let icon: any;
	export let pinId: string;
	export let pinned = false;
	export let showPin = false;
</script>

<div class="flex items-center w-full">
	<a
		{href}
		draggable="false"
		class="flex flex-1 h-[1.6875rem] items-center gap-2 rounded-xl px-2 text-[0.8125rem] hover:bg-gray-100 dark:hover:bg-gray-900 transition cursor-pointer select-none"
		on:click={async (e) => {
			if (e.metaKey || e.ctrlKey || e.shiftKey || e.button === 1) return;
			e.preventDefault();
			dispatch('navigate');
			goto(href);
			if ($mobile) {
				await tick();
				showSidebar.set(false);
			}
		}}
	>
		<div class="self-center">
			<svelte:component this={icon} className="size-3.5" strokeWidth="1.5" />
		</div>
		<div class="self-center truncate">{label}</div>
	</a>
	{#if showPin}
		<Tooltip content={pinned ? $i18n.t('Unpin from Sidebar') : $i18n.t('Pin to Sidebar')}>
			<button
				type="button"
				class="p-1 mr-1 rounded-lg hover:bg-gray-100/60 dark:hover:bg-gray-700/60 transition"
				on:click|preventDefault|stopPropagation={() => dispatch('togglePin', pinId)}
			>
				{#if pinned}
					<PinSlashIcon className="size-3.5" strokeWidth="1.5" />
				{:else}
					<PinIcon className="size-3.5" strokeWidth="1.5" />
				{/if}
			</button>
		</Tooltip>
	{/if}
</div>
