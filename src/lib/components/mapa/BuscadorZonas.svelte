<script lang="ts">
	import { getContext } from 'svelte';
	import { createEventDispatcher } from 'svelte';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;

	export let nombres: string[] = [];
	export let querying = false;
	export let latInput = '';
	export let lonInput = '';
	export let flotante = false;
	export let mostrarCoords = true;

	const dispatch = createEventDispatcher<{
		buscar: string;
		consultar: { lat: number; lon: number };
		ubicacion: void;
		abrirFiltros: void;
	}>();

	let q = '';
	let abierto = false;
	let coordsAbiertas = false;

	$: qNorm = q
		.trim()
		.normalize('NFD')
		.replace(/\p{M}/gu, '')
		.toLowerCase();
	$: sugerencias =
		qNorm.length >= 1
			? nombres
					.filter((n) =>
						n
							.normalize('NFD')
							.replace(/\p{M}/gu, '')
							.toLowerCase()
							.includes(qNorm)
					)
					.slice(0, 12)
			: [];

	const elegir = (nombre: string) => {
		q = nombre;
		abierto = false;
		dispatch('buscar', nombre);
	};

	const onConsultarCoords = () => {
		const lat = Number(String(latInput ?? '').trim());
		const lon = Number(String(lonInput ?? '').trim());
		if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
		dispatch('consultar', { lat, lon });
	};
</script>

<div class="relative space-y-2 {flotante ? '' : ''}">
	<div class="flex gap-2">
		<div class="relative flex-1 min-w-0">
			<input
				class="input-brand {!flotante ? '' : 'shadow-lg bg-white/95 dark:bg-gray-950/95 backdrop-blur'}"
				type="search"
				placeholder={$i18n.t('Search reservoir / zone…')}
				bind:value={q}
				aria-label={$i18n.t('Reservoir or zone')}
				autocomplete="off"
				on:focus={() => (abierto = true)}
				on:input={() => (abierto = true)}
				on:keydown={(e) => {
					if (e.key === 'Enter' && sugerencias[0]) {
						e.preventDefault();
						elegir(sugerencias[0]);
					}
					if (e.key === 'Escape') abierto = false;
				}}
			/>
			{#if abierto && sugerencias.length}
				<ul
					class="absolute z-40 mt-1 max-h-56 w-full overflow-y-auto rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-950 shadow-lg text-sm"
					role="listbox"
				>
					{#each sugerencias as nombre}
						<li>
							<button
								type="button"
								class="w-full text-left px-3 py-2 hover:bg-brand-50 dark:hover:bg-brand-950/50"
								on:click={() => elegir(nombre)}
							>
								{nombre}
							</button>
						</li>
					{/each}
				</ul>
			{/if}
		</div>
		{#if flotante}
			<button
				type="button"
				class="btn-secondary !px-3 shadow-lg bg-white/95 dark:bg-gray-950/95"
				on:click={() => dispatch('abrirFiltros')}
				aria-label={$i18n.t('Filters')}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.75"
					stroke="currentColor"
					class="size-5"
					aria-hidden="true"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M10.5 6h9.75M10.5 6a1.5 1.5 0 1 1-3 0m3 0a1.5 1.5 0 1 0-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m-9.75 0h9.75"
					/>
				</svg>
			</button>
		{/if}
	</div>

	{#if mostrarCoords}
		<details bind:open={coordsAbiertas} class="text-sm">
			<summary class="cursor-pointer text-xs font-medium text-gray-500 dark:text-gray-400">
				{$i18n.t('Coordinates')}
			</summary>
			<div class="mt-2 flex flex-wrap items-end gap-2">
				<label class="flex flex-col gap-1 text-xs text-gray-500">
					{$i18n.t('Lat')}
					<input class="input-brand !min-h-9 w-28" bind:value={latInput} inputmode="decimal" />
				</label>
				<label class="flex flex-col gap-1 text-xs text-gray-500">
					{$i18n.t('Lon')}
					<input class="input-brand !min-h-9 w-28" bind:value={lonInput} inputmode="decimal" />
				</label>
				<button
					type="button"
					class="btn-secondary !min-h-9"
					disabled={querying}
					on:click={onConsultarCoords}
				>
					{$i18n.t('Consult point')}
				</button>
				<button
					type="button"
					class="btn-secondary !min-h-9"
					disabled={querying}
					on:click={() => dispatch('ubicacion')}
				>
					{$i18n.t('Use my location')}
				</button>
			</div>
		</details>
	{/if}
</div>
