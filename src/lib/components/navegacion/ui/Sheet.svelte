<script lang="ts">
	import { createEventDispatcher, onDestroy, tick } from 'svelte';
	import { fade, fly } from 'svelte/transition';

	/** Whether the sheet is open. */
	export let open = false;
	/** Title announced to assistive tech and shown in the header when provided. */
	export let title = '';
	/** Extra classes for the panel. */
	export let className = '';
	/** z-index utility class. */
	export let zIndexClass = 'z-50';

	const dispatch = createEventDispatcher<{ close: void }>();

	let panel: HTMLDivElement | null = null;
	let previouslyFocused: HTMLElement | null = null;

	const FOCUSABLE =
		'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

	const cerrar = () => {
		open = false;
		dispatch('close');
	};

	const onKeydown = (e: KeyboardEvent) => {
		if (!open) return;
		if (e.key === 'Escape') {
			e.preventDefault();
			cerrar();
			return;
		}
		if (e.key !== 'Tab' || !panel) return;
		const nodes = Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
			(el) => !el.hasAttribute('disabled') && el.offsetParent !== null
		);
		if (!nodes.length) return;
		const first = nodes[0];
		const last = nodes[nodes.length - 1];
		if (e.shiftKey && document.activeElement === first) {
			e.preventDefault();
			last.focus();
		} else if (!e.shiftKey && document.activeElement === last) {
			e.preventDefault();
			first.focus();
		}
	};

	$: if (open) {
		previouslyFocused = document.activeElement as HTMLElement | null;
		tick().then(() => {
			const first = panel?.querySelector<HTMLElement>(FOCUSABLE);
			first?.focus();
		});
		document.body.style.overflow = 'hidden';
	} else if (previouslyFocused) {
		document.body.style.overflow = '';
		previouslyFocused.focus?.();
		previouslyFocused = null;
	}

	onDestroy(() => {
		document.body.style.overflow = '';
	});
</script>

<svelte:window on:keydown={onKeydown} />

{#if open}
	<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
	<div
		class="fixed inset-0 {zIndexClass} flex items-end justify-end md:items-stretch"
		role="presentation"
	>
		<div
			class="absolute inset-0 bg-black/50"
			transition:fade={{ duration: 150 }}
			on:click={cerrar}
		/>

		<div
			bind:this={panel}
			class="relative flex h-[min(92dvh,40rem)] w-full flex-col rounded-t-2xl bg-white dark:bg-gray-950 shadow-xl md:ml-auto md:h-full md:max-w-md md:rounded-none md:rounded-l-2xl {className}"
			role="dialog"
			aria-modal="true"
			aria-label={title || undefined}
			tabindex="-1"
			in:fly={{ x: typeof window !== 'undefined' && window.matchMedia('(min-width: 768px)').matches ? 40 : 0, y: typeof window !== 'undefined' && window.matchMedia('(min-width: 768px)').matches ? 0 : 80, duration: 180 }}
			out:fly={{ x: typeof window !== 'undefined' && window.matchMedia('(min-width: 768px)').matches ? 40 : 0, y: typeof window !== 'undefined' && window.matchMedia('(min-width: 768px)').matches ? 0 : 80, duration: 140 }}
			on:click|stopPropagation
		>
			{#if title || $$slots.header}
				<div
					class="flex items-center justify-between gap-2 border-b border-gray-100 dark:border-gray-850 px-4 py-3 shrink-0"
				>
					{#if $$slots.header}
						<slot name="header" />
					{:else}
						<h2 class="text-sm font-semibold tracking-tight text-brand-900 dark:text-brand-50">
							{title}
						</h2>
					{/if}
					<button
						type="button"
						class="btn-ghost !min-h-8 !px-2 text-xs"
						on:click={cerrar}
						aria-label="Close"
					>
						✕
					</button>
				</div>
			{/if}
			<div class="flex-1 min-h-0 overflow-y-auto px-4 py-3 pb-safe-bottom">
				<slot />
			</div>
			{#if $$slots.footer}
				<div class="shrink-0 border-t border-gray-100 dark:border-gray-850 px-4 py-3 pb-safe-bottom">
					<slot name="footer" />
				</div>
			{/if}
		</div>
	</div>
{/if}
