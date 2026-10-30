<script lang="ts">
	import { getContext, onDestroy, onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import {
		ErroresValidacion,
		generarDeclaracion,
		getDeclaracionSchema,
		getDeclaracionStatus,
		validarDeclaracion,
		validarPasoDeclaracion,
		type DeclaracionSchema,
		type ErrorValidacion,
		type PasoSchema
	} from '$lib/apis/declaracion';
	import PasoForm from './PasoForm.svelte';
	import RevisionPanel from './RevisionPanel.svelte';
	import BorradoresPanel from './BorradoresPanel.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import { borradorActivoId, borradoresRepo, type BorradorEntrada } from './borradores';
	import { traducirError } from './i18n';

	const AUTOGUARDADO_MS = 2000;

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let token = '';

	let loading = true;
	let errorMsg = '';
	let limitaciones = '';
	let schema: DeclaracionSchema | null = null;
	let paso = 1;
	let datos: Record<string, unknown> = {};
	let errores: ErrorValidacion[] = [];
	let matriculaFinal = '';
	let busy = false;
	let generating = false;
	let ttlBorradores = 90;
	let preguntarBorrarBorrador = false;

	let autoguardadoPendiente: ReturnType<typeof setTimeout> | null = null;
	let ultimoGuardado = '';

	const instantanea = () => JSON.stringify({ paso, datos });

	const autoguardar = async () => {
		autoguardadoPendiente = null;
		const id = get(borradorActivoId);
		const entrada = get(borradoresRepo.lista).find((b) => b.id === id);
		if (!entrada) return;
		const snap = instantanea();
		if (snap === ultimoGuardado) return;
		ultimoGuardado = snap;
		try {
			await borradoresRepo.guardar({ ...entrada, dr_paso: paso, dr_datos: datos });
		} catch (e: any) {
			toast.error(String(e?.message || e));
		}
	};

	const programarAutoguardado = (activo: string | null) => {
		if (!activo || instantanea() === ultimoGuardado) return;
		if (autoguardadoPendiente) clearTimeout(autoguardadoPendiente);
		autoguardadoPendiente = setTimeout(autoguardar, AUTOGUARDADO_MS);
	};

	$: (datos, paso, programarAutoguardado($borradorActivoId));

	onDestroy(() => {
		if (autoguardadoPendiente) {
			clearTimeout(autoguardadoPendiente);
			autoguardar();
		}
	});

	$: totalPasos = schema?.total_pasos ?? 8;
	$: pasoRevision = schema?.paso_revision?.indice ?? 8;
	$: pasosDatos = schema?.pasos ?? [];
	$: tituloActual =
		paso === pasoRevision
			? $i18n.t(schema?.paso_revision?.titulo || 'Review and generate')
			: $i18n.t(pasosDatos.find((p) => p.indice === paso)?.titulo || '');
	$: pasoActualCampos = (pasosDatos.find((p) => p.indice === paso)?.campos || []) as PasoSchema['campos'];
	$: pasosIndicador = [
		...pasosDatos.map((p) => ({ indice: p.indice, titulo: p.titulo })),
		{
			indice: pasoRevision,
			titulo: schema?.paso_revision?.titulo || 'Review and generate'
		}
	];

	// Derived from the schema instead of hard-coding step numbers / option strings.
	const buscarCampo = (clave: string) =>
		pasosDatos.flatMap((p) => p.campos).find((c) => c.clave === clave);
	$: pasoLugar = pasosDatos.find((p) => p.campos.some((c) => c.clave === 'embalses_seleccionados'))
		?.indice;
	$: pasoEmbarcacion = pasosDatos.find((p) =>
		p.campos.some((c) => c.clave === 'embarcacion_declarada_antes')
	)?.indice;
	// The "already declared" option is the one that reveals the registration field.
	$: valorYaDeclarada = (buscarCampo('embarcacion_matricula')?.mostrar_si as any)?.eq?.[1];

	const pad = (n: number) => String(n).padStart(2, '0');
	// Local date (toISOString would give yesterday's date around midnight in Spain).
	const hoyISO = () => {
		const d = new Date();
		return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
	};

	const aplicarIniciales = (pasos: PasoSchema[]) => {
		const next = { ...datos };
		for (const p of pasos) {
			for (const c of p.campos) {
				if (next[c.clave] !== undefined && next[c.clave] !== null && next[c.clave] !== '') {
					continue;
				}
				if (c.inicial_hoy) next[c.clave] = hoyISO();
				else if (c.valor_inicial !== undefined) next[c.clave] = c.valor_inicial;
				else if (c.tipo === 'multiselect') next[c.clave] = [];
				else if (c.tipo === 'checkbox') next[c.clave] = false;
			}
		}
		datos = next;
	};

	const aplicarQueryHandoff = () => {
		const params = new URLSearchParams(
			typeof window !== 'undefined' ? window.location.search : $page.url.search
		);
		const embalses = params
			.getAll('embalse')
			.map((s) => s.trim())
			.filter(Boolean);
		const otros = params.get('otros')?.trim();
		if (!embalses.length && !otros) return;

		const next = { ...datos };
		const sel = Array.isArray(next.embalses_seleccionados)
			? [...(next.embalses_seleccionados as string[])]
			: [];
		for (const embalse of embalses) {
			if (!sel.includes(embalse)) sel.push(embalse);
		}
		next.embalses_seleccionados = sel;
		if (otros) {
			const prev = String(next.embalses_otros || '').trim();
			next.embalses_otros = prev ? `${prev}, ${otros}` : otros;
		}
		datos = next;
		if (pasoLugar) paso = pasoLugar;

		goto('/declaracion', { replaceState: true, noScroll: true });
	};

	// Preview only; the authoritative value comes from the backend in the review step.
	const hintMatricula = (
		datos: Record<string, unknown>,
		valorYaDeclarada: unknown
	): string | null => {
		if (datos.embarcacion_declarada_antes === valorYaDeclarada) return null;
		const dni = String(datos.declarante_dni || '')
			.replace(/[^0-9A-Za-z]/g, '')
			.toUpperCase();
		const digitos = dni.replace(/\D/g, '');
		if (digitos.length < 3) return null;
		let letra = '';
		if (/[A-Z]$/.test(dni)) letra = dni.slice(-1);
		else if (/^[A-Z]/.test(dni)) letra = dni[0];
		if (!letra) return null;
		const corr = Number(datos.embarcacion_correlativo) || 1;
		const n = Math.max(1, Math.min(999, corr));
		return `CHMS-${digitos.slice(-3)}-${letra}-${String(n).padStart(3, '0')}`;
	};

	$: matriculaHint = hintMatricula(datos, valorYaDeclarada);

	const revisar = async () => {
		matriculaFinal = '';
		try {
			const res = await validarDeclaracion(token, datos);
			errores = res.errores || [];
			matriculaFinal = res.matricula || '';
		} catch (e: any) {
			toast.error(String(e?.message || e));
		}
	};

	onMount(async () => {
		// The wizard starts with a blank form; never autosave it over a draft edited earlier.
		borradorActivoId.set(null);
		try {
			const status = await getDeclaracionStatus(token);
			ttlBorradores = status.borradores_ttl_dias ?? ttlBorradores;
			if (!status.available) {
				errorMsg = $i18n.t(
					'The declaration template is not available yet. Wait for the docs pack seed.'
				);
				loading = false;
				return;
			}
			limitaciones = status.limitaciones_mvp || '';
			schema = await getDeclaracionSchema(token);
			aplicarIniciales(schema.pasos);
			aplicarQueryHandoff();
		} catch (e: any) {
			errorMsg = String(e?.message || e || $i18n.t('Could not load the declaration wizard'));
			toast.error(errorMsg);
		} finally {
			loading = false;
		}
	});

	const anterior = () => {
		errores = [];
		if (paso > 1) paso -= 1;
	};

	const siguiente = async () => {
		if (!schema || busy) return;
		busy = true;
		errores = [];
		try {
			if (paso < pasoRevision) {
				const res = await validarPasoDeclaracion(token, paso, datos);
				if (!res.ok) {
					errores = res.errores || [];
					return;
				}
				paso += 1;
				if (paso === pasoRevision) await revisar();
			}
		} catch (e: any) {
			toast.error(String(e?.message || e));
		} finally {
			busy = false;
		}
	};

	const generar = async () => {
		if (generating) return;
		generating = true;
		errores = [];
		try {
			// The backend validates again in /generar; a 422 carries the structured errors.
			const { blob, filename } = await generarDeclaracion(token, datos);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = filename;
			a.click();
			// Revoking synchronously can abort the download in some browsers.
			setTimeout(() => URL.revokeObjectURL(url), 1000);
			toast.success($i18n.t('Declaration downloaded'));
			if (get(borradorActivoId)) preguntarBorrarBorrador = true;
		} catch (e: any) {
			if (e instanceof ErroresValidacion) {
				errores = e.errores;
				toast.error($i18n.t('Fix validation errors before generating'));
			} else {
				toast.error(String(e?.message || e));
			}
		} finally {
			generating = false;
		}
	};

	const onCargarBorrador = async (entrada: BorradorEntrada) => {
		datos = structuredClone(entrada.dr_datos || {});
		paso = entrada.dr_paso || 1;
		errores = [];
		if (schema) aplicarIniciales(schema.pasos);
		ultimoGuardado = instantanea();
		if (paso === pasoRevision) await revisar();
	};

	const borrarBorradorActivo = async () => {
		const id = get(borradorActivoId);
		if (!id) return;
		await borradoresRepo.eliminar(id);
		toast.success($i18n.t('Draft deleted'));
	};
</script>

{#if loading}
	<p class="text-sm text-gray-500">{$i18n.t('Loading…')}</p>
{:else if errorMsg}
	<div class="rounded-xl border border-amber-200 dark:border-amber-900 bg-amber-50 dark:bg-amber-950/40 px-4 py-3 text-sm">
		{errorMsg}
	</div>
{:else if schema}
	<div class="space-y-5">
		{#if limitaciones}
			<div
				class="rounded-xl border border-sky-200 dark:border-sky-900 bg-sky-50 dark:bg-sky-950/30 px-4 py-3 text-sm text-sky-950 dark:text-sky-100"
			>
				{$i18n.t(limitaciones)}
			</div>
		{/if}

		<BorradoresPanel
			{datos}
			{paso}
			ttlDias={ttlBorradores}
			onCargar={onCargarBorrador}
			onGuardado={() => (ultimoGuardado = instantanea())}
		/>

		<div class="space-y-3">
			<ol
				class="flex flex-wrap items-start gap-1 sm:gap-0 sm:justify-between"
				aria-label={$i18n.t('Declaration wizard steps')}
			>
				{#each pasosIndicador as item, idx (item.indice)}
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
							{#if idx < pasosIndicador.length - 1}
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
			<div class="flex items-center justify-between gap-2 text-sm">
				<span class="font-medium">
					{$i18n.t('Step')} {paso} {$i18n.t('of')} {totalPasos}: {tituloActual}
				</span>
				<span class="text-gray-500">{Math.round((paso / totalPasos) * 100)}%</span>
			</div>
			<div class="h-2 rounded-full bg-brand-100 dark:bg-brand-950 overflow-hidden">
				<div
					class="h-full bg-brand-700 dark:bg-accent-500 transition-all"
					style="width: {(paso / totalPasos) * 100}%"
				/>
			</div>
		</div>

		{#if errores.length}
			<ul
				class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/30 px-4 py-3 text-sm text-red-800 dark:text-red-200 space-y-1 list-disc list-inside"
			>
				{#each errores as err}
					<li>{traducirError($i18n.t, err)}</li>
				{/each}
			</ul>
		{/if}

		{#if paso < pasoRevision}
			<PasoForm campos={pasoActualCampos} bind:datos />
			{#if paso === pasoEmbarcacion && matriculaHint}
				<p class="text-sm text-sky-800 dark:text-sky-200">
					{$i18n.t('Registration that will be generated')}: <strong>{matriculaHint}</strong>
				</p>
			{/if}
		{:else}
			<div class="card-brand border-l-4 border-l-accent-500 px-4 py-3 space-y-1">
				<h2 class="text-sm font-semibold text-brand-800 dark:text-brand-100">
					{$i18n.t('Declaration summary')}
				</h2>
				<p class="text-xs text-gray-500 dark:text-gray-400">
					{$i18n.t('Review your answers below, then generate the official DOCX.')}
				</p>
			</div>
			<RevisionPanel pasos={pasosDatos} {datos} matricula={matriculaFinal} />
		{/if}

		<div class="flex flex-wrap gap-2 justify-between pt-2">
			<button
				type="button"
				class="rounded-xl border border-gray-200 dark:border-gray-700 px-4 py-2 text-sm disabled:opacity-40"
				disabled={paso <= 1 || busy || generating}
				on:click={anterior}
			>
				{$i18n.t('Previous')}
			</button>

			<div class="flex gap-2">
				{#if paso < pasoRevision}
					<button
						type="button"
						class="rounded-xl btn-brand px-4 py-2 text-sm font-medium disabled:opacity-40"
						disabled={busy || generating}
						on:click={siguiente}
					>
						{$i18n.t('Next')}
					</button>
				{:else}
					<button
						type="button"
						class="rounded-xl btn-brand px-4 py-2 text-sm font-medium disabled:opacity-40"
						disabled={generating}
						on:click={generar}
					>
						{generating ? $i18n.t('Generating…') : $i18n.t('Generate DOCX')}
					</button>
				{/if}
			</div>
		</div>
	</div>
{/if}

<ConfirmDialog
	bind:show={preguntarBorrarBorrador}
	title={$i18n.t('Keep the draft?')}
	message={$i18n.t(
		'The declaration has been generated. Do you want to keep this draft in your account or delete it?'
	)}
	cancelLabel={$i18n.t('Keep draft')}
	confirmLabel={$i18n.t('Delete draft')}
	onConfirm={borrarBorradorActivo}
/>
