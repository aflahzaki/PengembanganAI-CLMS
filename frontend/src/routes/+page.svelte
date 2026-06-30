<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getHealth, getDocxTemplates, uploadDocxTemplate, deleteDocxTemplate, getDocxTemplateHtml } from '$lib/api/client';
	import type { DocxTemplateInfo } from '$lib/api/client';
	import { docxTemplates, editorContent, showError, showSuccess } from '$lib/stores/contract';
	import TemplateCard from '$lib/components/TemplateCard.svelte';

	let healthStatus = $state<{ status: string; version: string; chroma_db_status: string; templates_loaded: number } | null>(null);
	let healthError = $state(false);
	let loadingTemplates = $state(true);
	let uploading = $state(false);
	let templateList = $state<DocxTemplateInfo[]>([]);

	let fileInput: HTMLInputElement | undefined = $state();
	let currentEditorContent = $state('');

	// Preview modal state
	let previewOpen = $state(false);
	let previewHtml = $state('');
	let previewName = $state('');
	let previewLoading = $state(false);

	onMount(async () => {
		try {
			healthStatus = await getHealth();
		} catch {
			healthError = true;
		}
	});

	onMount(async () => {
		await loadTemplates();
	});

	onMount(() => {
		const unsub = docxTemplates.subscribe((v) => {
			templateList = v;
		});
		return unsub;
	});

	onMount(() => {
		const unsub = editorContent.subscribe((v) => {
			currentEditorContent = v;
		});
		return unsub;
	});

	async function loadTemplates() {
		loadingTemplates = true;
		try {
			const data = await getDocxTemplates();
			docxTemplates.set(data);
		} catch {
			showError('Gagal memuat template DOCX. Pastikan backend berjalan.');
		} finally {
			loadingTemplates = false;
		}
	}

	function handleUseTemplate(template: DocxTemplateInfo) {
		if (currentEditorContent.length > 20 && currentEditorContent !== '<p></p>') {
			if (!confirm('Konten editor akan diganti dengan template baru. Lanjutkan?')) {
				return;
			}
		}
		goto(`/draft?mode=template&id=${encodeURIComponent(template.id)}`);
	}

	async function handleDeleteTemplate(template: DocxTemplateInfo) {
		if (!confirm(`Apakah Anda yakin ingin menghapus template "${template.name}"?`)) {
			return;
		}
		try {
			await deleteDocxTemplate(template.id);
			showSuccess(`Template "${template.name}" berhasil dihapus.`);
			await loadTemplates();
		} catch {
			showError('Gagal menghapus template.');
		}
	}

	function handleUploadClick() {
		fileInput?.click();
	}

	async function handleFileSelected(event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		if (!file.name.endsWith('.docx')) {
			showError('Hanya file .docx yang didukung.');
			input.value = '';
			return;
		}

		uploading = true;
		try {
			await uploadDocxTemplate(file);
			showSuccess(`Template "${file.name}" berhasil diupload.`);
			await loadTemplates();
		} catch {
			showError('Gagal mengupload template.');
		} finally {
			uploading = false;
			input.value = '';
		}
	}

	async function handlePreviewTemplate(template: DocxTemplateInfo) {
		previewName = template.name;
		previewOpen = true;
		previewLoading = true;
		previewHtml = '';
		try {
			const data = await getDocxTemplateHtml(template.id);
			previewHtml = data.html_content;
		} catch {
			previewHtml = '<p class="text-red-500">Gagal memuat preview template.</p>';
		} finally {
			previewLoading = false;
		}
	}

	function closePreview() {
		previewOpen = false;
		previewHtml = '';
		previewName = '';
	}

	function handlePreviewBackdropClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			closePreview();
		}
	}
</script>

<svelte:head>
	<title>Dashboard - CLMS</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<!-- Welcome Section -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900">Selamat Datang di CLMS</h1>
		<p class="mt-2 text-gray-600">Contract Lifecycle Management System untuk pengelolaan kontrak PLN</p>
	</div>

	<!-- Status Cards -->
	<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
		<!-- Backend Status -->
		<div class="card">
			<div class="flex items-center gap-3">
				<div class="w-10 h-10 rounded-lg flex items-center justify-center {healthStatus ? 'bg-green-100' : healthError ? 'bg-red-100' : 'bg-gray-100'}">
					{#if healthStatus}
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-green-600" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
						</svg>
					{:else if healthError}
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-600" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
						</svg>
					{:else}
						<div class="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-400"></div>
					{/if}
				</div>
				<div>
					<h3 class="text-sm font-medium text-gray-500">Status Backend</h3>
					<p class="text-lg font-semibold {healthStatus ? 'text-green-600' : healthError ? 'text-red-600' : 'text-gray-400'}">
						{healthStatus ? 'Terhubung' : healthError ? 'Tidak Terhubung' : 'Memeriksa...'}
					</p>
				</div>
			</div>
			{#if healthStatus}
				<div class="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500 space-y-1">
					<p>Versi: {healthStatus.version}</p>
					<p>ChromaDB: {healthStatus.chroma_db_status}</p>
					<p>Template: {healthStatus.templates_loaded} dimuat</p>
				</div>
			{/if}
		</div>

		<!-- Quick Stats -->
		<div class="card">
			<div class="flex items-center gap-3">
				<div class="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
					</svg>
				</div>
				<div>
					<h3 class="text-sm font-medium text-gray-500">Template DOCX</h3>
					<p class="text-lg font-semibold text-primary">
						{templateList.length}
					</p>
				</div>
			</div>
			<p class="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
				Template kontrak tersedia untuk digunakan
			</p>
		</div>

		<!-- Quick Action -->
		<div class="card flex flex-col justify-between">
			<div class="flex items-center gap-3">
				<div class="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary" viewBox="0 0 20 20" fill="currentColor">
						<path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
					</svg>
				</div>
				<div>
					<h3 class="text-sm font-medium text-gray-500">Aksi Cepat</h3>
					<p class="text-lg font-semibold text-gray-900">Buat Kontrak</p>
				</div>
			</div>
			<a href="/draft" class="btn-primary text-center mt-4 block">
				Mulai Draft Baru
			</a>
		</div>
	</div>

	<!-- Template Library Section -->
	<div class="mb-6">
		<div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4 gap-3">
			<h2 class="text-xl font-semibold text-gray-900">Template Library</h2>
			<div class="w-full sm:w-auto">
				<input
					type="file"
					accept=".docx"
					class="hidden"
					bind:this={fileInput}
					onchange={handleFileSelected}
				/>
				<button
					class="btn-primary flex items-center justify-center gap-2 w-full sm:w-auto"
					onclick={handleUploadClick}
					disabled={uploading}
				>
					{#if uploading}
						<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
						<span>Mengupload...</span>
					{:else}
						<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd" />
						</svg>
						<span>Upload Template Baru</span>
					{/if}
				</button>
			</div>
		</div>

		{#if loadingTemplates}
			<div class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
				<span class="ml-3 text-gray-600">Memuat template...</span>
			</div>
		{:else if templateList.length === 0}
			<div class="card text-center py-12">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-gray-300 mx-auto mb-4" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
				</svg>
				<p class="text-gray-500">Belum ada template. Upload template DOCX untuk memulai.</p>
			</div>
		{:else}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each templateList as template (template.id)}
					<TemplateCard
						{template}
						onUse={handleUseTemplate}
						onDelete={handleDeleteTemplate}
						onPreview={handlePreviewTemplate}
					/>
				{/each}
			</div>
		{/if}
	</div>
</div>

<!-- Preview Modal -->
{#if previewOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
		onclick={handlePreviewBackdropClick}
	>
		<div class="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col">
			<!-- Modal Header -->
			<div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
				<h3 class="font-semibold text-gray-900 text-lg">Preview: {previewName}</h3>
				<button
					onclick={closePreview}
					class="p-1 rounded-lg hover:bg-gray-100 text-gray-500 hover:text-gray-700"
					aria-label="Tutup"
				>
					<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
			<!-- Modal Body -->
			<div class="flex-1 overflow-y-auto px-6 py-4" style="max-height: 500px;">
				{#if previewLoading}
					<div class="flex items-center justify-center py-12">
						<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
						<span class="ml-3 text-gray-600">Memuat preview...</span>
					</div>
				{:else}
					<div class="prose prose-sm max-w-none template-preview">
						{@html previewHtml}
					</div>
				{/if}
			</div>
			<!-- Modal Footer -->
			<div class="px-6 py-4 border-t border-gray-200 flex justify-end">
				<button class="btn-secondary" onclick={closePreview}>Tutup</button>
			</div>
		</div>
	</div>
{/if}
