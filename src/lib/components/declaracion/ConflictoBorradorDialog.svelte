<script lang="ts">
	import { getContext } from 'svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import type { BorradorListado } from './borradores';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let show = false;
	export let borrador: BorradorListado | null = null;
	export let onResolver: (opcion: 'local' | 'servidor' | 'copia') => void = () => {};

	const fecha = (iso: string | undefined) => {
		if (!iso) return '—';
		const d = new Date(iso);
		return Number.isNaN(d.getTime()) ? iso : d.toLocaleString($i18n.language);
	};

	const elegir = (opcion: 'local' | 'servidor' | 'copia') => {
		show = false;
		onResolver(opcion);
	};
</script>

<Modal bind:show size="sm">
	{#if borrador}
		<div class="px-5 py-5 space-y-4 text-sm">
			<div>
				<h2 class="text-base font-medium">{$i18n.t('This draft was changed somewhere else')}</h2>
				<p class="mt-1 text-gray-500 dark:text-gray-400">
					{$i18n.t(
						'The copy on this device and the one saved in your account are different. Choose which one to keep.'
					)}
				</p>
			</div>

			<dl class="grid grid-cols-2 gap-3">
				<div class="rounded-xl border border-gray-200 dark:border-gray-800 px-3 py-2">
					<dt class="text-xs text-gray-500">{$i18n.t('This device')}</dt>
					<dd class="font-medium truncate">{borrador.nombre}</dd>
					<dd class="text-xs text-gray-500">
						{$i18n.t('Step')}
						{borrador.dr_paso} · {fecha(borrador.actualizado)}
					</dd>
				</div>
				<div class="rounded-xl border border-gray-200 dark:border-gray-800 px-3 py-2">
					<dt class="text-xs text-gray-500">{$i18n.t('Your account')}</dt>
					<dd class="font-medium truncate">{borrador.servidor?.nombre ?? '—'}</dd>
					<dd class="text-xs text-gray-500">
						{$i18n.t('Step')}
						{borrador.servidor?.dr_paso ?? '—'} · {fecha(borrador.servidor?.actualizado)}
					</dd>
				</div>
			</dl>

			<div class="flex flex-col gap-2">
				<button
					type="button"
					class="rounded-xl btn-brand px-3 py-2 font-medium"
					on:click={() => elegir('local')}
				>
					{$i18n.t('Keep this device version')}
				</button>
				<button
					type="button"
					class="rounded-xl border border-gray-200 dark:border-gray-700 px-3 py-2"
					on:click={() => elegir('servidor')}
				>
					{$i18n.t('Keep the account version')}
				</button>
				<button
					type="button"
					class="rounded-xl border border-gray-200 dark:border-gray-700 px-3 py-2"
					on:click={() => elegir('copia')}
				>
					{$i18n.t('Keep both (save this device version as a copy)')}
				</button>
			</div>
		</div>
	{/if}
</Modal>
