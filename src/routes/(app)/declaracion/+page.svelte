<script lang="ts">
	import { getContext } from 'svelte';
	import DeclaracionWizard from '$lib/components/declaracion/DeclaracionWizard.svelte';
	import PageShell from '$lib/components/navegacion/ui/PageShell.svelte';

	const i18n = getContext('i18n');
	$: _lang = $i18n.language;
</script>

<PageShell
	title={$i18n.t('Declaration')}
	subtitle={$i18n.t(
		'Fill in the responsible navigation declaration (Miño-Sil MVP) and download the official DOCX.'
	)}
	contentClass="max-w-6xl mx-auto w-full"
>
	<DeclaracionWizard token={localStorage.token} />
</PageShell>
