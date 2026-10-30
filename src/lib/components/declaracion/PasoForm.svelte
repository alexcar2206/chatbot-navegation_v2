<script lang="ts">
	import { getContext, tick } from 'svelte';
	import type { CampoSchema, ErrorValidacion } from '$lib/apis/declaracion';
	import { evaluarMostrarSi } from './borradores';
	import { traducirError } from './i18n';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let campos: CampoSchema[] = [];
	export let datos: Record<string, unknown> = {};
	export let errores: ErrorValidacion[] = [];

	const OPCION_VACIA = '— No aplica —';
	const MULTI_BUSCADOR_MIN = 8;

	/** Per-field HTML attributes for better mobile keyboards. */
	const ATRIBUTOS_CAMPO: Record<
		string,
		{ inputmode?: string; autocomplete?: string; autocapitalize?: string }
	> = {
		declarante_email: { inputmode: 'email', autocomplete: 'email' },
		declarante_telefono: { inputmode: 'tel', autocomplete: 'tel' },
		declarante_cp: { inputmode: 'numeric', autocomplete: 'postal-code' },
		declarante_dni: { autocapitalize: 'characters', autocomplete: 'off' },
		firma_dni: { autocapitalize: 'characters', autocomplete: 'off' },
		declarante_nombre: { autocomplete: 'name' },
		declarante_direccion: { autocomplete: 'street-address' },
		declarante_localidad: { autocomplete: 'address-level2' },
		declarante_provincia: { autocomplete: 'address-level1' }
	};

	const ANCHO_COMPLETO = new Set([
		'embalses_seleccionados',
		'embalses_otros',
		'declarante_direccion',
		'aceptacion'
	]);

	let filtroMulti: Record<string, string> = {};

	$: visibles = campos.filter((c) => evaluarMostrarSi(c.mostrar_si as any, datos));
	$: erroresPorClave = (() => {
		const map: Record<string, ErrorValidacion[]> = {};
		for (const err of errores) {
			const clave = err.params?.clave;
			if (!clave) continue;
			(map[clave] ??= []).push(err);
		}
		return map;
	})();

	const setValor = (clave: string, valor: unknown) => {
		datos = { ...datos, [clave]: valor };
	};

	const toggleMulti = (clave: string, opcion: string, checked: boolean) => {
		const actual = Array.isArray(datos[clave]) ? [...(datos[clave] as string[])] : [];
		const next = checked ? [...new Set([...actual, opcion])] : actual.filter((x) => x !== opcion);
		setValor(clave, next);
	};

	export const enfocarPrimerError = async () => {
		await tick();
		const primera = visibles.find((c) => erroresPorClave[c.clave]?.length);
		if (!primera) return;
		document.getElementById(`dr-${primera.clave}`)?.focus?.();
		document.getElementById(`dr-${primera.clave}`)?.scrollIntoView?.({
			behavior: 'smooth',
			block: 'center'
		});
	};

	const opcionesFiltradas = (campo: CampoSchema) => {
		const ops = campo.opciones || [];
		const q = (filtroMulti[campo.clave] || '')
			.normalize('NFD')
			.replace(/\p{M}/gu, '')
			.toLowerCase()
			.trim();
		if (!q) return ops;
		return ops.filter((op) =>
			$i18n
				.t(op)
				.normalize('NFD')
				.replace(/\p{M}/gu, '')
				.toLowerCase()
				.includes(q)
		);
	};
</script>

<div class="form-brand grid gap-4 sm:grid-cols-2">
	{#each visibles as campo (campo.clave)}
		{@const errs = erroresPorClave[campo.clave] || []}
		{@const attrs = ATRIBUTOS_CAMPO[campo.clave] || {}}
		{@const full = ANCHO_COMPLETO.has(campo.clave) || campo.tipo === 'multiselect' || campo.tipo === 'checkbox'}
		<div class="space-y-1.5 {full ? 'sm:col-span-2' : ''}">
			{#if campo.tipo !== 'checkbox'}
				<label
					class="block text-sm font-medium text-gray-800 dark:text-gray-100"
					for="dr-{campo.clave}"
				>
					{$i18n.t(campo.etiqueta)}
					{#if campo.obligatorio}<span class="text-red-500">*</span>{/if}
				</label>
			{/if}

			{#if campo.tipo === 'texto'}
				<input
					id="dr-{campo.clave}"
					type="text"
					class="input-brand {errs.length ? 'border-red-400 focus:ring-red-400/40' : ''}"
					value={datos[campo.clave] ?? ''}
					aria-invalid={errs.length ? 'true' : undefined}
					aria-describedby={errs.length ? `err-${campo.clave}` : undefined}
					inputmode={attrs.inputmode}
					autocomplete={attrs.autocomplete}
					autocapitalize={attrs.autocapitalize}
					on:input={(e) => setValor(campo.clave, e.currentTarget.value)}
				/>
			{:else if campo.tipo === 'numero'}
				<input
					id="dr-{campo.clave}"
					type="number"
					min={campo.minimo}
					max={campo.maximo}
					class="input-brand {errs.length ? 'border-red-400 focus:ring-red-400/40' : ''}"
					value={datos[campo.clave] ?? ''}
					aria-invalid={errs.length ? 'true' : undefined}
					aria-describedby={errs.length ? `err-${campo.clave}` : undefined}
					inputmode="numeric"
					on:input={(e) => {
						const v = e.currentTarget.value;
						setValor(campo.clave, v === '' ? '' : Number(v));
					}}
				/>
			{:else if campo.tipo === 'fecha'}
				<input
					id="dr-{campo.clave}"
					type="date"
					class="input-brand {errs.length ? 'border-red-400 focus:ring-red-400/40' : ''}"
					value={datos[campo.clave] ?? ''}
					aria-invalid={errs.length ? 'true' : undefined}
					aria-describedby={errs.length ? `err-${campo.clave}` : undefined}
					on:input={(e) => setValor(campo.clave, e.currentTarget.value)}
				/>
			{:else if campo.tipo === 'select'}
				<select
					id="dr-{campo.clave}"
					class="input-brand {errs.length ? 'border-red-400 focus:ring-red-400/40' : ''}"
					value={datos[campo.clave] ?? (campo.permite_vacio ? OPCION_VACIA : '')}
					aria-invalid={errs.length ? 'true' : undefined}
					aria-describedby={errs.length ? `err-${campo.clave}` : undefined}
					on:change={(e) => {
						const v = e.currentTarget.value;
						setValor(campo.clave, v === OPCION_VACIA ? '' : v);
					}}
				>
					{#if campo.permite_vacio || !campo.obligatorio}
						<option value={OPCION_VACIA}>{$i18n.t(OPCION_VACIA)}</option>
					{/if}
					{#each campo.opciones || [] as op}
						<option value={op}>{$i18n.t(op)}</option>
					{/each}
				</select>
			{:else if campo.tipo === 'multiselect'}
				{@const seleccion = Array.isArray(datos[campo.clave])
					? (datos[campo.clave] as string[])
					: []}
				{@const conBuscador = (campo.opciones || []).length > MULTI_BUSCADOR_MIN}
				<div class="space-y-2">
					{#if seleccion.length}
						<div class="flex flex-wrap gap-1.5">
							{#each seleccion as op}
								<span class="chip chip-active">
									{$i18n.t(op)}
									<button
										type="button"
										class="ml-0.5 text-brand-700 dark:text-brand-200"
										aria-label={$i18n.t('Remove')}
										on:click={() => toggleMulti(campo.clave, op, false)}
									>
										×
									</button>
								</span>
							{/each}
						</div>
					{/if}
					{#if conBuscador}
						<input
							type="search"
							class="input-brand !min-h-9"
							placeholder={$i18n.t('Search…')}
							bind:value={filtroMulti[campo.clave]}
						/>
					{/if}
					<div
						id="dr-{campo.clave}"
						class="max-h-48 overflow-y-auto rounded-xl border {errs.length
							? 'border-red-400'
							: 'border-gray-200 dark:border-gray-700'} px-3 py-2 space-y-1.5"
						aria-invalid={errs.length ? 'true' : undefined}
						aria-describedby={errs.length ? `err-${campo.clave}` : undefined}
					>
						{#each opcionesFiltradas(campo) as op}
							<label class="flex items-center gap-2 text-sm cursor-pointer">
								<input
									type="checkbox"
									class="rounded"
									checked={seleccion.includes(op)}
									on:change={(e) => toggleMulti(campo.clave, op, e.currentTarget.checked)}
								/>
								<span>{$i18n.t(op)}</span>
							</label>
						{/each}
					</div>
				</div>
			{:else if campo.tipo === 'checkbox'}
				<label class="flex items-start gap-2 text-sm cursor-pointer" for="dr-{campo.clave}">
					<input
						id="dr-{campo.clave}"
						type="checkbox"
						class="mt-0.5 rounded"
						checked={Boolean(datos[campo.clave])}
						aria-invalid={errs.length ? 'true' : undefined}
						aria-describedby={errs.length ? `err-${campo.clave}` : undefined}
						on:change={(e) => setValor(campo.clave, e.currentTarget.checked)}
					/>
					<span>
						{$i18n.t(campo.etiqueta)}
						{#if campo.obligatorio}<span class="text-red-500">*</span>{/if}
					</span>
				</label>
			{:else}
				<input
					id="dr-{campo.clave}"
					type="text"
					class="input-brand {errs.length ? 'border-red-400 focus:ring-red-400/40' : ''}"
					value={datos[campo.clave] ?? ''}
					on:input={(e) => setValor(campo.clave, e.currentTarget.value)}
				/>
			{/if}

			{#if errs.length}
				<ul id="err-{campo.clave}" class="space-y-0.5">
					{#each errs as err}
						<li class="text-xs text-red-600 dark:text-red-300">{traducirError($i18n.t, err)}</li>
					{/each}
				</ul>
			{/if}

			{#if campo.ayuda}
				<p class="text-xs text-gray-500 dark:text-gray-400">{$i18n.t(campo.ayuda)}</p>
			{/if}
		</div>
	{/each}
</div>
