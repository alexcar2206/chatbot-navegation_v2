<script lang="ts">
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let pasos: { indice: number; titulo: string }[] = [];
	export let paso = 1;
	export let orientacion: 'horizontal' | 'vertical' | 'compacto' = 'horizontal';
	export let onIrA: ((indice: number) => void) | null = null;
</script>

{#if orientacion === 'compacto'}
	<button
		type="button"
		class="w-full text-left rounded-xl border border-brand-100 dark:border-brand-800 bg-white/80 dark:bg-brand-950/40 px-3 py-2"
		on:click
	>
		<div class="flex items-center justify-between gap-2 text-sm">
			<span class="font-medium text-brand-900 dark:text-brand-50">
				{$i18n.t('Step')} {paso} {$i18n.t('of')} {pasos.length}:
				{$i18n.t(pasos.find((p) => p.indice === paso)?.titulo || '')}
			</span>
			<span class="text-gray-500 tabular-nums">{Math.round((paso / pasos.length) * 100)}%</span>
		</div>
		<div class="mt-2 h-1.5 rounded-full bg-brand-100 dark:bg-brand-950 overflow-hidden">
			<div
				class="h-full bg-brand-700 dark:bg-accent-500 transition-all"
				style="width: {(paso / pasos.length) * 100}%"
			/>
		</div>
	</button>
{:else if orientacion === 'vertical'}
	<ol class="space-y-1" aria-label={$i18n.t('Declaration wizard steps')}>
		{#each pasos as item, idx (item.indice)}
			{@const done = paso > item.indice}
			{@const active = paso === item.indice}
			{@const clickable = !!onIrA && item.indice < paso}
			<li>
				<button
					type="button"
					class="w-full flex items-start gap-2.5 rounded-xl px-2 py-2 text-left transition {active
						? 'bg-brand-50 dark:bg-brand-950/50'
						: clickable
							? 'hover:bg-gray-50 dark:hover:bg-gray-900/50'
							: 'opacity-70'}"
					disabled={!clickable && !active}
					on:click={() => clickable && onIrA?.(item.indice)}
				>
					<span
						class="flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold border-2 {done
							? 'bg-accent-500 border-accent-500 text-white'
							: active
								? 'bg-brand-700 border-brand-700 text-white'
								: 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 text-gray-500'}"
						aria-current={active ? 'step' : undefined}
					>
						{idx + 1}
					</span>
					<span
						class="text-xs leading-snug pt-1 {active
							? 'text-brand-800 dark:text-brand-100 font-medium'
							: 'text-gray-500 dark:text-gray-400'}"
					>
						{$i18n.t(item.titulo)}
					</span>
				</button>
			</li>
		{/each}
	</ol>
{:else}
	<ol
		class="flex flex-wrap items-start gap-1 sm:gap-0 sm:justify-between"
		aria-label={$i18n.t('Declaration wizard steps')}
	>
		{#each pasos as item, idx (item.indice)}
			{@const done = paso > item.indice}
			{@const active = paso === item.indice}
			<li class="flex items-center gap-1 sm:flex-1 sm:min-w-0 sm:flex-col sm:gap-1.5">
				<div class="flex items-center gap-1 sm:flex-col sm:w-full">
					<span
						class="flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold border-2 transition {done
							? 'bg-accent-500 border-accent-500 text-white'
							: active
								? 'bg-brand-700 border-brand-700 text-white'
								: 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 text-gray-500'}"
						aria-current={active ? 'step' : undefined}
					>
						{idx + 1}
					</span>
					{#if idx < pasos.length - 1}
						<span
							class="hidden sm:block h-0.5 flex-1 mx-1 rounded-full {done
								? 'bg-accent-400'
								: 'bg-gray-200 dark:bg-gray-800'}"
							aria-hidden="true"
						/>
					{/if}
				</div>
				<span
					class="hidden sm:block text-[0.65rem] leading-tight text-center px-0.5 line-clamp-2 w-full {active
						? 'text-brand-800 dark:text-brand-100 font-medium'
						: 'text-gray-500 dark:text-gray-400'}"
				>
					{$i18n.t(item.titulo)}
				</span>
			</li>
		{/each}
	</ol>
{/if}
