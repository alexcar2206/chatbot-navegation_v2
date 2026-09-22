<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import {
		generarDeclaracion,
		getDeclaracionSchema,
		getDeclaracionStatus,
		validarDeclaracion,
		validarPasoDeclaracion,
		type DeclaracionSchema,
		type PasoSchema
	} from '$lib/apis/declaracion';
	import PasoForm from './PasoForm.svelte';
	import RevisionPanel from './RevisionPanel.svelte';
	import BorradoresPanel from './BorradoresPanel.svelte';
	import type { BorradorEntrada } from './borradores';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let token = '';

	const EMBARCACION_NUEVA = 'Embarcación no declarada anteriormente';
	const PASO_LUGAR = 5;

	let loading = true;
	let errorMsg = '';
	let limitaciones = '';
	let schema: DeclaracionSchema | null = null;
	let paso = 1;
	let datos: Record<string, unknown> = {};
	let errores: string[] = [];
	let busy = false;
	let generating = false;

	$: totalPasos = schema?.total_pasos ?? 8;
	$: pasoRevision = schema?.paso_revision?.indice ?? 8;
	$: pasosDatos = schema?.pasos ?? [];
	$: tituloActual =
		paso === pasoRevision
			? schema?.paso_revision?.titulo || $i18n.t('Review and generate')
			: pasosDatos.find((p) => p.indice === paso)?.titulo || '';
	$: pasoActualCampos = (pasosDatos.find((p) => p.indice === paso)?.campos || []) as PasoSchema['campos'];

	const hoyISO = () => new Date().toISOString().slice(0, 10);

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
		const embalse = params.get('embalse')?.trim();
		const otros = params.get('otros')?.trim();
		if (!embalse && !otros) return;

		const next = { ...datos };
		if (embalse) {
			const sel = Array.isArray(next.embalses_seleccionados)
				? [...(next.embalses_seleccionados as string[])]
				: [];
			if (!sel.includes(embalse)) sel.push(embalse);
			next.embalses_seleccionados = sel;
		}
		if (otros) {
			next.embalses_otros = otros;
		}
		datos = next;
		paso = PASO_LUGAR;

		goto('/declaracion', { replaceState: true, noScroll: true });
	};

	const hintMatricula = (): string | null => {
		if (datos.embarcacion_declarada_antes === EMBARCACION_NUEVA || !datos.embarcacion_declarada_antes) {
			const dni = String(datos.declarante_dni || '').replace(/[^0-9A-Za-z]/g, '').toUpperCase();
			const digitos = dni.replace(/\D/g, '');
			if (digitos.length < 3) return null;
			let letra = '';
			if (/[A-Z]$/.test(dni)) letra = dni.slice(-1);
			else if (/^[A-Z]/.test(dni)) letra = dni[0];
			if (!letra) return null;
			const corr = Number(datos.embarcacion_correlativo) || 1;
			const n = Math.max(1, Math.min(999, corr));
			return `CHMS-${digitos.slice(-3)}-${letra}-${String(n).padStart(3, '0')}`;
		}
		return null;
	};

	$: matriculaHint = hintMatricula();

	onMount(async () => {
		try {
			const status = await getDeclaracionStatus(token);
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
			const res = await validarDeclaracion(token, datos);
			if (!res.ok) {
				errores = res.errores || [];
				toast.error($i18n.t('Fix validation errors before generating'));
				return;
			}
			const { blob, filename } = await generarDeclaracion(token, datos);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = filename;
			a.click();
			URL.revokeObjectURL(url);
			toast.success($i18n.t('Declaration downloaded'));
		} catch (e: any) {
			toast.error(String(e?.message || e));
		} finally {
			generating = false;
		}
	};

	const onCargarBorrador = (entrada: BorradorEntrada) => {
		datos = structuredClone(entrada.dr_datos || {});
		paso = entrada.dr_paso || 1;
		errores = [];
		if (schema) aplicarIniciales(schema.pasos);
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
				{limitaciones}
			</div>
		{/if}

		<BorradoresPanel {datos} {paso} onCargar={onCargarBorrador} />

		<div class="space-y-2">
			<div class="flex items-center justify-between gap-2 text-sm">
				<span class="font-medium">
					{$i18n.t('Step')} {paso} {$i18n.t('of')} {totalPasos}: {tituloActual}
				</span>
				<span class="text-gray-500">{Math.round((paso / totalPasos) * 100)}%</span>
			</div>
			<div class="h-2 rounded-full bg-gray-100 dark:bg-gray-850 overflow-hidden">
				<div
					class="h-full bg-gray-900 dark:bg-gray-100 transition-all"
					style="width: {(paso / totalPasos) * 100}%"
				/>
			</div>
		</div>

		{#if errores.length}
			<ul
				class="rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/30 px-4 py-3 text-sm text-red-800 dark:text-red-200 space-y-1 list-disc list-inside"
			>
				{#each errores as err}
					<li>{err}</li>
				{/each}
			</ul>
		{/if}

		{#if paso < pasoRevision}
			<PasoForm campos={pasoActualCampos} bind:datos />
			{#if paso === 2 && matriculaHint}
				<p class="text-sm text-sky-800 dark:text-sky-200">
					{$i18n.t('Registration that will be generated')}: <strong>{matriculaHint}</strong>
				</p>
			{/if}
		{:else}
			<RevisionPanel pasos={pasosDatos} {datos} />
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
						class="rounded-xl bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900 px-4 py-2 text-sm font-medium disabled:opacity-40"
						disabled={busy || generating}
						on:click={siguiente}
					>
						{$i18n.t('Next')}
					</button>
				{:else}
					<button
						type="button"
						class="rounded-xl bg-gray-900 text-white dark:bg-gray-100 dark:text-gray-900 px-4 py-2 text-sm font-medium disabled:opacity-40"
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
