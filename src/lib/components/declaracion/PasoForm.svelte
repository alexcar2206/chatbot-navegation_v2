<script lang="ts">
	import { getContext } from 'svelte';
	import type { CampoSchema } from '$lib/apis/declaracion';
	import { evaluarMostrarSi } from './borradores';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let campos: CampoSchema[] = [];
	export let datos: Record<string, unknown> = {};

	const OPCION_VACIA = '— No aplica —';

	$: visibles = campos.filter((c) => evaluarMostrarSi(c.mostrar_si as any, datos));

	const setValor = (clave: string, valor: unknown) => {
		datos = { ...datos, [clave]: valor };
	};

	const toggleMulti = (clave: string, opcion: string, checked: boolean) => {
		const actual = Array.isArray(datos[clave]) ? [...(datos[clave] as string[])] : [];
		const next = checked ? [...new Set([...actual, opcion])] : actual.filter((x) => x !== opcion);
		setValor(clave, next);
	};
</script>

<div class="space-y-4">
	{#each visibles as campo (campo.clave)}
		<div class="space-y-1.5">
			{#if campo.tipo !== 'checkbox'}
				<label class="block text-sm font-medium text-gray-800 dark:text-gray-100" for="dr-{campo.clave}">
					{campo.etiqueta}
					{#if campo.obligatorio}<span class="text-red-500">*</span>{/if}
				</label>
			{/if}

			{#if campo.tipo === 'texto'}
				<input
					id="dr-{campo.clave}"
					type="text"
					class="w-full rounded-xl border border-gray-200 dark:border-gray-800 bg-transparent px-3 py-2 text-sm"
					value={datos[campo.clave] ?? ''}
					on:input={(e) => setValor(campo.clave, e.currentTarget.value)}
				/>
			{:else if campo.tipo === 'numero'}
				<input
					id="dr-{campo.clave}"
					type="number"
					min={campo.minimo}
					max={campo.maximo}
					class="w-full rounded-xl border border-gray-200 dark:border-gray-800 bg-transparent px-3 py-2 text-sm"
					value={datos[campo.clave] ?? ''}
					on:input={(e) => {
						const v = e.currentTarget.value;
						setValor(campo.clave, v === '' ? '' : Number(v));
					}}
				/>
			{:else if campo.tipo === 'fecha'}
				<input
					id="dr-{campo.clave}"
					type="date"
					class="w-full rounded-xl border border-gray-200 dark:border-gray-800 bg-transparent px-3 py-2 text-sm"
					value={datos[campo.clave] ?? ''}
					on:input={(e) => setValor(campo.clave, e.currentTarget.value)}
				/>
			{:else if campo.tipo === 'select'}
				<select
					id="dr-{campo.clave}"
					class="w-full rounded-xl border border-gray-200 dark:border-gray-800 bg-transparent px-3 py-2 text-sm dark:bg-gray-900"
					value={datos[campo.clave] ?? (campo.permite_vacio ? OPCION_VACIA : '')}
					on:change={(e) => {
						const v = e.currentTarget.value;
						setValor(campo.clave, v === OPCION_VACIA ? '' : v);
					}}
				>
					{#if campo.permite_vacio || !campo.obligatorio}
						<option value={OPCION_VACIA}>{OPCION_VACIA}</option>
					{/if}
					{#each campo.opciones || [] as op}
						<option value={op}>{op}</option>
					{/each}
				</select>
			{:else if campo.tipo === 'multiselect'}
				<div
					id="dr-{campo.clave}"
					class="max-h-48 overflow-y-auto rounded-xl border border-gray-200 dark:border-gray-800 px-3 py-2 space-y-1.5"
				>
					{#each campo.opciones || [] as op}
						<label class="flex items-center gap-2 text-sm cursor-pointer">
							<input
								type="checkbox"
								class="rounded"
								checked={Array.isArray(datos[campo.clave]) &&
									(datos[campo.clave] as string[]).includes(op)}
								on:change={(e) => toggleMulti(campo.clave, op, e.currentTarget.checked)}
							/>
							<span>{op}</span>
						</label>
					{/each}
				</div>
			{:else if campo.tipo === 'checkbox'}
				<label class="flex items-start gap-2 text-sm cursor-pointer" for="dr-{campo.clave}">
					<input
						id="dr-{campo.clave}"
						type="checkbox"
						class="mt-0.5 rounded"
						checked={Boolean(datos[campo.clave])}
						on:change={(e) => setValor(campo.clave, e.currentTarget.checked)}
					/>
					<span>
						{campo.etiqueta}
						{#if campo.obligatorio}<span class="text-red-500">*</span>{/if}
					</span>
				</label>
			{:else}
				<input
					id="dr-{campo.clave}"
					type="text"
					class="w-full rounded-xl border border-gray-200 dark:border-gray-800 bg-transparent px-3 py-2 text-sm"
					value={datos[campo.clave] ?? ''}
					on:input={(e) => setValor(campo.clave, e.currentTarget.value)}
				/>
			{/if}

			{#if campo.ayuda}
				<p class="text-xs text-gray-500 dark:text-gray-400">{campo.ayuda}</p>
			{/if}
		</div>
	{/each}
</div>
