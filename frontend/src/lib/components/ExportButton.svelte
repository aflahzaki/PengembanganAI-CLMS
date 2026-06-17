<script lang="ts">
	import { onMount } from 'svelte';
	import { exportToDocx } from '$lib/api/client';
	import { editorContent, showError, showSuccess } from '$lib/stores/contract';

	let exporting = $state(false);
	let content = $state('');

	onMount(() => {
		const unsub = editorContent.subscribe((v) => { content = v; });
		return unsub;
	});

	async function handleExport() {
		if (!content || content === '<p></p>') {
			showError('Tidak ada konten untuk diekspor. Generate draft terlebih dahulu.');
			return;
		}

		exporting = true;
		try {
			await exportToDocx(content, 'kontrak_draft.docx');
			showSuccess('Dokumen berhasil diunduh!');
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : 'Gagal mengekspor dokumen.';
			showError(message);
		} finally {
			exporting = false;
		}
	}

	let hasContent = $derived(content.length > 0 && content !== '<p></p>');
</script>

<button
	class="btn-secondary flex items-center gap-2 {!hasContent ? 'opacity-50 cursor-not-allowed' : ''}"
	onclick={handleExport}
	disabled={exporting || !hasContent}
>
	{#if exporting}
		<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
		<span>Mengekspor...</span>
	{:else}
		<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
			<path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd" />
		</svg>
		<span>Export DOCX</span>
	{/if}
</button>
