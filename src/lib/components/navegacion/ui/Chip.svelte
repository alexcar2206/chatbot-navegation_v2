<script lang="ts">
	export let active = false;
	export let count: number | null = null;
	export let disabled = false;
	/** Extra classes for the button. */
	export let className = '';
</script>

<button
	type="button"
	class="chip {active ? 'chip-active' : ''} {className}"
	{disabled}
	aria-pressed={active}
	on:click
>
	<slot />
	{#if count != null}
		<span
			class="rounded-full px-1.5 py-px text-[0.65rem] tabular-nums {active
				? 'bg-brand-700/15 dark:bg-brand-300/20'
				: 'bg-gray-100 dark:bg-gray-800'}"
		>
			{count}
		</span>
	{/if}
</button>
