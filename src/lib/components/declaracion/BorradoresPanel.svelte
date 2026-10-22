<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { user } from '$lib/stores';
	import {
		eliminarBorrador,
		leerBorradores,
		limpiarBorradoresCompartidos,
		MAX_BORRADORES,
		nombreBorradorSugerido,
		nuevoId,
		upsertBorrador,
		escribirBorradores,
		type BorradorEntrada
	} from './borradores';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let datos: Record<string, unknown> = {};
	export let paso = 1;
	export let onCargar: (entrada: BorradorEntrada) => void = () => {};

	let lista: BorradorEntrada[] = [];
	let nombre = '';
	/** Draft currently being edited (loaded or last saved); "Save" updates it in place. */
	let borradorActivoId: string | null = null;

	$: userId = $user?.id ?? '';
	$: canWrite = Boolean(userId);

	const refresh = () => {
		lista = leerBorradores(userId);
	};

	$: userId, refresh();

	onMount(() => {
		limpiarBorradoresCompartidos();
		refresh();
		nombre = nombreBorradorSugerido(datos);
	});

	const guardar = (comoNuevo = false) => {
		if (!userId) return;
		try {
			const existente =
				!comoNuevo && borradorActivoId && lista.some((b) => b.id === borradorActivoId);
			const entrada: BorradorEntrada = {
				id: existente ? (borradorActivoId as string) : nuevoId(),
				nombre: (nombre || '').trim() || nombreBorradorSugerido(datos),
				actualizado: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z'),
				dr_paso: paso,
				dr_datos: structuredClone(datos)
			};
			lista = upsertBorrador(lista, entrada);
			escribirBorradores(userId, lista);
			borradorActivoId = entrada.id;
			toast.success($i18n.t('Draft saved'));
			refresh();
		} catch (e: any) {
			if (String(e?.message || e).startsWith('MAX_BORRADORES')) {
				toast.error($i18n.t('Maximum drafts reached. Delete one before saving another.'));
			} else {
				toast.error(String(e?.message || e));
			}
		}
	};

	const cargar = (entrada: BorradorEntrada) => {
		borradorActivoId = entrada.id;
		nombre = entrada.nombre;
		onCargar(entrada);
		toast.success($i18n.t('Draft loaded'));
	};

	const borrar = (id: string) => {
		if (!userId) return;
		lista = eliminarBorrador(lista, id);
		escribirBorradores(userId, lista);
		if (borradorActivoId === id) borradorActivoId = null;
		toast.success($i18n.t('Draft deleted'));
	};
</script>

<div class="rounded-xl border border-gray-200 dark:border-gray-800 px-4 py-3 space-y-3">
	<div class="flex items-center justify-between gap-2">
		<h3 class="text-sm font-semibold">{$i18n.t('Drafts')}</h3>
		<span class="text-xs text-gray-500">{lista.length}/{MAX_BORRADORES}</span>
	</div>

	<div class="flex flex-col sm:flex-row gap-2">
		<input
			type="text"
			class="flex-1 rounded-xl border border-gray-200 dark:border-gray-800 bg-transparent px-3 py-2 text-sm disabled:opacity-40"
			placeholder={$i18n.t('Draft name')}
			bind:value={nombre}
			disabled={!canWrite}
		/>
		<button
			type="button"
			class="rounded-xl bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900 px-3 py-2 text-sm font-medium disabled:opacity-40"
			disabled={!canWrite}
			on:click={() => guardar()}
		>
			{$i18n.t('Save draft')}
		</button>
		{#if borradorActivoId}
			<button
				type="button"
				class="rounded-xl border border-gray-200 dark:border-gray-700 px-3 py-2 text-sm disabled:opacity-40"
				disabled={!canWrite}
				on:click={() => guardar(true)}
			>
				{$i18n.t('Save as new draft')}
			</button>
		{/if}
	</div>

	<p class="text-xs text-amber-700 dark:text-amber-300">
		{$i18n.t('Drafts are stored only in this browser and include personal data.')}
	</p>

	{#if lista.length === 0}
		<p class="text-xs text-gray-500">{$i18n.t('No drafts saved in this browser yet.')}</p>
	{:else}
		<ul class="space-y-2">
			{#each lista as b (b.id)}
				<li
					class="flex flex-col sm:flex-row sm:items-center gap-2 rounded-lg border border-gray-100 dark:border-gray-850 px-3 py-2 text-sm"
				>
					<div class="flex-1 min-w-0">
						<div class="font-medium truncate">{b.nombre}</div>
						<div class="text-xs text-gray-500">
							{$i18n.t('Step')} {b.dr_paso} · {b.actualizado}
						</div>
					</div>
					<div class="flex gap-2 shrink-0">
						<button
							type="button"
							class="rounded-lg border border-gray-200 dark:border-gray-700 px-2 py-1 text-xs"
							on:click={() => cargar(b)}
						>
							{$i18n.t('Load')}
						</button>
						<button
							type="button"
							class="rounded-lg border border-red-200 text-red-700 dark:border-red-900 dark:text-red-300 px-2 py-1 text-xs disabled:opacity-40"
							disabled={!canWrite}
							on:click={() => borrar(b.id)}
						>
							{$i18n.t('Delete')}
						</button>
					</div>
				</li>
			{/each}
		</ul>
	{/if}
</div>
