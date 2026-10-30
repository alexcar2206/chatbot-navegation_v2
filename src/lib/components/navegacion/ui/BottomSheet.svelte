<script lang="ts">
	import { createEventDispatcher, onDestroy, onMount } from 'svelte';

	export type AlturaSheet = 'peek' | 'media' | 'completa';

	/** Current snap height. */
	export let altura: AlturaSheet = 'peek';
	/** Peek height in CSS pixels (summary strip). */
	export let peekPx = 96;
	/** Whether the sheet is visible. */
	export let open = true;
	/** Extra classes on the sheet panel. */
	export let className = '';

	const dispatch = createEventDispatcher<{ altura: AlturaSheet }>();

	const SNAPS: AlturaSheet[] = ['peek', 'media', 'completa'];
	const MEDIA_FRAC = 0.5;
	const COMPLETA_FRAC = 0.92;
	const SETTLE_MS = 220;

	let panel: HTMLDivElement | null = null;
	let viewportH = 0;
	let dragging = false;
	let startY = 0;
	let startOffset = 0;
	let dragOffset = 0;
	let reducedMotion = false;
	let raf: number | null = null;
	let ro: ResizeObserver | null = null;

	$: alturas = {
		peek: peekPx,
		media: Math.round(viewportH * MEDIA_FRAC),
		completa: Math.round(viewportH * COMPLETA_FRAC)
	};

	$: targetH = alturas[altura] || peekPx;
	/** With bottom:0 and height=completa, translate down by (completa - visible). Completa → 0 (no clip). */
	$: offsetY = dragging ? dragOffset : Math.max(0, alturas.completa - targetH);
	$: transitioning = !dragging && !reducedMotion;

	const medir = () => {
		const parent = panel?.offsetParent as HTMLElement | null;
		const h = parent?.clientHeight;
		viewportH = h && h > 0 ? h : typeof window !== 'undefined' ? window.innerHeight : 800;
	};

	const setAltura = (next: AlturaSheet) => {
		if (altura === next) return;
		altura = next;
		dispatch('altura', next);
	};

	const snapMasCercano = (offset: number): AlturaSheet => {
		const visibles = SNAPS.map((s) => ({
			s,
			h: alturas[s],
			dist: Math.abs(alturas.completa - alturas[s] - offset)
		}));
		visibles.sort((a, b) => a.dist - b.dist);
		return visibles[0]?.s ?? 'peek';
	};

	const onPointerDown = (e: PointerEvent) => {
		if (e.button !== 0) return;
		dragging = true;
		startY = e.clientY;
		startOffset = offsetY;
		dragOffset = offsetY;
		(e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId);
	};

	const onPointerMove = (e: PointerEvent) => {
		if (!dragging) return;
		const delta = e.clientY - startY;
		const min = 0;
		const max = Math.max(0, alturas.completa - alturas.peek);
		dragOffset = Math.min(max, Math.max(min, startOffset + delta));
	};

	const onPointerUp = () => {
		if (!dragging) return;
		dragging = false;
		setAltura(snapMasCercano(dragOffset));
	};

	onMount(() => {
		medir();
		reducedMotion =
			typeof window !== 'undefined' &&
			window.matchMedia('(prefers-reduced-motion: reduce)').matches;
		window.addEventListener('resize', medir);
		const parent = panel?.offsetParent;
		if (parent && typeof ResizeObserver !== 'undefined') {
			ro = new ResizeObserver(() => medir());
			ro.observe(parent);
		}
	});

	onDestroy(() => {
		if (typeof window !== 'undefined') window.removeEventListener('resize', medir);
		ro?.disconnect();
		if (raf != null) cancelAnimationFrame(raf);
	});
</script>

{#if open}
	<div
		bind:this={panel}
		class="pointer-events-auto absolute inset-x-0 bottom-0 z-30 flex flex-col rounded-t-2xl border border-brand-100/80 dark:border-brand-800 bg-white dark:bg-gray-950 shadow-[0_-8px_30px_rgba(11,79,108,0.12)] dark:shadow-[0_-8px_30px_rgba(0,0,0,0.45)] {className}"
		style="height: {alturas.completa}px; transform: translateY({offsetY}px); transition: {transitioning
			? `transform ${SETTLE_MS}ms cubic-bezier(0.22, 1, 0.36, 1)`
			: 'none'}; will-change: transform;"
		role="dialog"
		aria-modal="false"
		aria-label={$$props['aria-label'] || 'Panel'}
	>
		<div
			class="shrink-0 touch-none select-none cursor-grab active:cursor-grabbing px-4 pt-2 pb-1"
			style="touch-action: none;"
			on:pointerdown={onPointerDown}
			on:pointermove={onPointerMove}
			on:pointerup={onPointerUp}
			on:pointercancel={onPointerUp}
			role="presentation"
		>
			<div class="mx-auto mb-2 h-1 w-10 rounded-full bg-gray-300 dark:bg-gray-600" aria-hidden="true" />
			{#if $$slots.handle}
				<slot name="handle" />
			{/if}
		</div>

		<div
			class="flex flex-1 min-h-0 flex-col px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] overflow-hidden"
		>
			<slot />
		</div>
	</div>
{/if}
