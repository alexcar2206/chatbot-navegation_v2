<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { user } from '$lib/stores';
	import { ErrorBorrador } from '$lib/apis/declaracion';
	import {
		borradorActivoId,
		borradoresRepo,
		limpiarBorradoresCompartidos,
		nombreBorradorSugerido,
		nuevoId,
		type BorradorEntrada,
		type BorradorListado
	} from './borradores';
	import EstadoSyncBadge from './EstadoSyncBadge.svelte';
	import ConflictoBorradorDialog from './ConflictoBorradorDialog.svelte';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let datos: Record<string, unknown> = {};
	export let paso = 1;
	export let ttlDias = 90;
	export let onCargar: (entrada: BorradorEntrada) => void = () => {};
	/** Called after a manual save, so the wizard does not autosave the same content again. */
	export let onGuardado: () => void = () => {};

	const { lista, estadoGlobal } = borradoresRepo;

	let nombre = '';
	let guardando = false;
	let conflictoAbierto = false;
	let borradorConflicto: BorradorListado | null = null;

	$: userId = $user?.id ?? '';
	$: canWrite = Boolean(userId);
	$: activo = $lista.find((b) => b.id === $borradorActivoId) ?? null;

	onMount(async () => {
		limpiarBorradoresCompartidos();
		nombre = nombreBorradorSugerido(datos);
		if (!userId) return;
		const { migrados } = await borradoresRepo.iniciar(userId, localStorage.token);
		if (migrados > 0) {
			toast.info(
				$i18n.t('{{count}} drafts from this browser are being uploaded to your account', {
					count: migrados
				})
			);
		}
	});

	const mensajeError = (e: unknown) => {
		if (e instanceof ErrorBorrador && e.codigo === 'MAX_BORRADORES') {
			return $i18n.t('Maximum drafts reached. Delete one before saving another.');
		}
		return String((e as any)?.message || e);
	};

	const guardar = async (comoNuevo = false) => {
		if (!userId || guardando) return;
		guardando = true;
		const id = !comoNuevo && activo ? activo.id : nuevoId();
		try {
			await borradoresRepo.guardar({
				id,
				nombre: (nombre || '').trim() || nombreBorradorSugerido(datos),
				actualizado: '',
				dr_paso: paso,
				dr_datos: datos
			});
			borradorActivoId.set(id);
			onGuardado();
			toast.success($i18n.t('Draft saved'));
		} catch (e) {
			toast.error(mensajeError(e));
		} finally {
			guardando = false;
		}
	};

	const cargar = async (b: BorradorListado) => {
		try {
			const entrada = await borradoresRepo.cargar(b.id);
			borradorActivoId.set(b.id);
			nombre = entrada.nombre;
			onCargar(entrada);
			toast.success($i18n.t('Draft loaded'));
		} catch (e) {
			toast.error($i18n.t('Could not load the draft. Check your connection.'));
		}
	};

	const borrar = async (id: string) => {
		if (!userId) return;
		await borradoresRepo.eliminar(id);
		toast.success($i18n.t('Draft deleted'));
	};

	const abrirConflicto = (b: BorradorListado) => {
		borradorConflicto = b;
		conflictoAbierto = true;
	};

	const resolver = async (opcion: 'local' | 'servidor' | 'copia') => {
		if (!borradorConflicto) return;
		const id = borradorConflicto.id;
		await borradoresRepo.resolverConflicto(id, opcion);
		if (opcion !== 'local' && $borradorActivoId === id) {
			const entrada = await borradoresRepo.cargar(id);
			nombre = entrada.nombre;
			onCargar(entrada);
		}
		toast.success($i18n.t('Conflict resolved'));
	};

	const fecha = (iso: string) => {
		const d = new Date(iso);
		return Number.isNaN(d.getTime()) ? iso : d.toLocaleString($i18n.language);
	};
</script>

<div class="rounded-xl border border-gray-200 dark:border-gray-800 px-4 py-3 space-y-3">
	<div class="flex items-center justify-between gap-2">
		<h3 class="text-sm font-semibold">{$i18n.t('Drafts')}</h3>
		{#if $lista.length}
			<EstadoSyncBadge estado={$estadoGlobal} />
		{/if}
	</div>

	<div class="flex flex-col sm:flex-row gap-2">
		<input
			type="text"
			class="flex-1 rounded-xl border border-gray-200 dark:border-gray-800 bg-transparent px-3 py-2 text-sm disabled:opacity-40"
			placeholder={$i18n.t('Draft name')}
			maxlength="120"
			bind:value={nombre}
			disabled={!canWrite}
		/>
		<button
			type="button"
			class="rounded-xl bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900 px-3 py-2 text-sm font-medium disabled:opacity-40"
			disabled={!canWrite || guardando}
			on:click={() => guardar()}
		>
			{$i18n.t('Save draft')}
		</button>
		{#if activo}
			<button
				type="button"
				class="rounded-xl border border-gray-200 dark:border-gray-700 px-3 py-2 text-sm disabled:opacity-40"
				disabled={!canWrite || guardando}
				on:click={() => guardar(true)}
			>
				{$i18n.t('Save as new draft')}
			</button>
		{/if}
	</div>

	{#if activo}
		<p class="text-xs text-gray-500 dark:text-gray-400">
			{$i18n.t('Editing “{{name}}”. Changes are saved automatically.', { name: activo.nombre })}
		</p>
	{/if}

	<p class="text-xs text-gray-500 dark:text-gray-400">
		{#if ttlDias > 0}
			{$i18n.t(
				'Drafts include personal data. They are saved to your account and deleted after {{days}} days without changes; this browser keeps a copy to work offline.',
				{ days: ttlDias }
			)}
		{:else}
			{$i18n.t(
				'Drafts include personal data. They are saved to your account; this browser keeps a copy to work offline.'
			)}
		{/if}
	</p>

	{#if $lista.length === 0}
		<p class="text-xs text-gray-500">{$i18n.t('No drafts saved yet.')}</p>
	{:else}
		<ul class="space-y-2">
			{#each $lista as b (b.id)}
				<li
					class="flex flex-col sm:flex-row sm:items-center gap-2 rounded-lg border px-3 py-2 text-sm {b.id ===
					$borradorActivoId
						? 'border-brand-300 dark:border-brand-700 bg-brand-50/50 dark:bg-brand-950/30'
						: 'border-gray-100 dark:border-gray-850'}"
				>
					<div class="flex-1 min-w-0">
						<div class="font-medium truncate">{b.nombre}</div>
						<div class="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-gray-500">
							<span>{$i18n.t('Step')} {b.dr_paso} · {fecha(b.actualizado)}</span>
							<EstadoSyncBadge estado={b.sync} />
						</div>
						{#if b.error}
							<div class="text-xs text-red-700 dark:text-red-300">{b.error}</div>
						{/if}
					</div>
					<div class="flex gap-2 shrink-0">
						{#if b.sync === 'conflicto'}
							<button
								type="button"
								class="rounded-lg border border-red-200 text-red-700 dark:border-red-900 dark:text-red-300 px-2 py-1 text-xs"
								on:click={() => abrirConflicto(b)}
							>
								{$i18n.t('Resolve')}
							</button>
						{/if}
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

<ConflictoBorradorDialog
	bind:show={conflictoAbierto}
	borrador={borradorConflicto}
	onResolver={resolver}
/>
