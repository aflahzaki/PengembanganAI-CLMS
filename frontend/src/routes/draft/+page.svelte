<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import TipTapEditor from '$lib/components/TipTapEditor.svelte';
	import ExportButton from '$lib/components/ExportButton.svelte';
	import { getDocxTemplateHtml, generateAiDraft } from '$lib/api/client';
	import type { DocxVariableInfo } from '$lib/api/client';
	import { editorContent, documentName, draftMode, showError, showSuccess } from '$lib/stores/contract';

	let activeMode = $state<'template' | 'generate'>('template');
	let templateLoading = $state(false);
	let templateName = $state('');
	let templateVariables = $state<DocxVariableInfo[]>([]);
	let currentEditorContent = $state('');

	// AI Generate Mode state
	let aiDescription = $state('');
	let aiNamaPihak1 = $state('');
	let aiNamaPihak2 = $state('');
	let aiNomorKontrak = $state('');
	let aiTanggal = $state('');
	let aiNilaiKontrak = $state('');
	let aiReferenceFile = $state<File | null>(null);
	let aiGenerating = $state(false);

	// Variable counter state
	let variableCount = $state(0);
	let debounceTimer: ReturnType<typeof setTimeout> | null = null;

	function countVariables(html: string): number {
		if (!html) return 0;
		const matches = html.match(/\[[^\]]+\]/g);
		return matches ? matches.length : 0;
	}

	onMount(() => {
		const unsub = draftMode.subscribe((v) => {
			activeMode = v;
		});
		return unsub;
	});

	onMount(() => {
		const unsub = editorContent.subscribe((v) => {
			currentEditorContent = v;
			// Debounced variable count update
			if (debounceTimer) clearTimeout(debounceTimer);
			debounceTimer = setTimeout(() => {
				variableCount = countVariables(v);
			}, 1000);
		});
		return unsub;
	});

	onMount(() => {
		// Read URL params
		const mode = page.url.searchParams.get('mode');
		const id = page.url.searchParams.get('id');

		if (mode === 'template' && id) {
			activeMode = 'template';
			draftMode.set('template');
			loadTemplate(id);
		} else if (mode === 'generate') {
			activeMode = 'generate';
			draftMode.set('generate');
		}
	});

	function hasExistingContent(): boolean {
		return currentEditorContent.length > 20 && currentEditorContent !== '<p></p>';
	}

	function getFriendlyErrorMessage(err: unknown): string {
		const message = err instanceof Error ? err.message : String(err);
		if (message.includes('429')) {
			return 'AI sedang sibuk. Coba lagi dalam 1 menit.';
		}
		if (message.includes('401') || message.includes('Unauthorized')) {
			return 'API key tidak valid. Hubungi administrator.';
		}
		if (message.toLowerCase().includes('timeout')) {
			return 'Proses terlalu lama. Coba lagi.';
		}
		return 'Terjadi kesalahan. Silakan coba lagi.';
	}

	async function loadTemplate(id: string) {
		if (hasExistingContent()) {
			if (!confirm('Konten editor akan diganti dengan template baru. Lanjutkan?')) {
				return;
			}
		}

		templateLoading = true;
		try {
			const data = await getDocxTemplateHtml(id);
			templateName = data.name;
			templateVariables = data.variables;
			editorContent.set(data.html_content);
			documentName.set(data.name);
			// Immediately count variables from loaded content
			variableCount = countVariables(data.html_content);
			window.scrollTo({ top: 0, behavior: 'smooth' });
		} catch (err: unknown) {
			showError(getFriendlyErrorMessage(err));
		} finally {
			templateLoading = false;
		}
	}

	function switchMode(mode: 'template' | 'generate') {
		activeMode = mode;
		draftMode.set(mode);
	}

	function handleFileChange(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			aiReferenceFile = target.files[0];
		} else {
			aiReferenceFile = null;
		}
	}

	async function handleAiGenerate() {
		if (!aiDescription.trim()) {
			showError('Deskripsi kebutuhan tidak boleh kosong.');
			return;
		}

		if (hasExistingContent()) {
			if (!confirm('Konten editor akan diganti dengan template baru. Lanjutkan?')) {
				return;
			}
		}

		aiGenerating = true;
		try {
			const variables: Record<string, string> = {};
			if (aiNamaPihak1.trim()) variables['Nama Pihak 1'] = aiNamaPihak1.trim();
			if (aiNamaPihak2.trim()) variables['Nama Pihak 2'] = aiNamaPihak2.trim();
			if (aiNomorKontrak.trim()) variables['Nomor Kontrak'] = aiNomorKontrak.trim();
			if (aiTanggal.trim()) variables['Tanggal'] = aiTanggal.trim();
			if (aiNilaiKontrak.trim()) variables['Nilai Kontrak'] = aiNilaiKontrak.trim();

			const result = await generateAiDraft(
				aiDescription.trim(),
				variables,
				aiReferenceFile || undefined
			);

			editorContent.set(result.html_content);
			documentName.set(aiDescription.trim().substring(0, 50));
			showSuccess('Draft kontrak berhasil di-generate oleh AI.');
			variableCount = countVariables(result.html_content);
			window.scrollTo({ top: 0, behavior: 'smooth' });
		} catch (err: unknown) {
			showError(getFriendlyErrorMessage(err));
		} finally {
			aiGenerating = false;
		}
	}

	function handlePrintPreview() {
		window.print();
	}

	function getVariableColor(type: string): string {
		switch (type) {
			case 'dynamic': return '#FFEB3B';
			case 'editable': return '#FFF9C4';
			case 'instruction': return 'transparent';
			default: return '#FFF9C4';
		}
	}

	function getVariableLabel(type: string): string {
		switch (type) {
			case 'dynamic': return 'Wajib diisi';
			case 'editable': return 'Perlu dipilih/diubah';
			case 'instruction': return 'Instruksi';
			default: return '';
		}
	}
</script>

<svelte:head>
	<title>Buat Draft Kontrak - CLMS</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<!-- Page Header -->
	<div class="mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 print:hidden">
		<div>
			<h1 class="text-2xl font-bold text-gray-900">Buat Draft Kontrak</h1>
			<p class="mt-1 text-gray-600">Pilih mode pembuatan draft kontrak</p>
		</div>
		<div class="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
			<button
				class="btn-secondary flex items-center justify-center gap-2 w-full sm:w-auto"
				onclick={handlePrintPreview}
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M5 4v3H4a2 2 0 00-2 2v3a2 2 0 002 2h1v2a2 2 0 002 2h6a2 2 0 002-2v-2h1a2 2 0 002-2V9a2 2 0 00-2-2h-1V4a2 2 0 00-2-2H7a2 2 0 00-2 2zm8 0H7v3h6V4zm0 8H7v4h6v-4z" clip-rule="evenodd" />
				</svg>
				<span>Preview Cetak</span>
			</button>
			<ExportButton />
		</div>
	</div>

	<!-- Mode Tabs -->
	<div class="mb-6 print:hidden">
		<div class="flex border-b border-gray-200">
			<button
				class="px-4 sm:px-6 py-3 text-sm font-medium border-b-2 transition-colors duration-150 {activeMode === 'template' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
				onclick={() => switchMode('template')}
			>
				<span class="flex items-center gap-2">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
					</svg>
					Dari Template
				</span>
			</button>
			<button
				class="px-4 sm:px-6 py-3 text-sm font-medium border-b-2 transition-colors duration-150 {activeMode === 'generate' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
				onclick={() => switchMode('generate')}
			>
				<span class="flex items-center gap-2">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
						<path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z" />
					</svg>
					Generate Baru (AI)
				</span>
			</button>
		</div>
	</div>

	<!-- Variable Counter Badge -->
	{#if variableCount > 0}
		<div class="mb-4 print:hidden">
			<span class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
				</svg>
				{variableCount} variabel perlu diisi
			</span>
		</div>
	{/if}

	<!-- Mode Content -->
	{#if activeMode === 'template'}
		<!-- Template Mode -->
		<div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
			<!-- Left Panel: Variable List -->
			<div class="lg:col-span-3 print:hidden">
				<div class="sticky top-4">
					{#if templateLoading}
						<div class="card">
							<div class="flex items-center justify-center py-8">
								<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
								<span class="ml-3 text-gray-600 text-sm">Memuat template...</span>
							</div>
						</div>
					{:else if templateName}
						<div class="card">
							<h3 class="font-semibold text-gray-900 mb-3 text-sm">{templateName}</h3>
							<div class="mb-4">
								<h4 class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Legenda Variabel</h4>
								<div class="space-y-1.5">
									<div class="flex items-center gap-2 text-xs">
										<span class="w-4 h-4 rounded" style="background-color: #FFEB3B;"></span>
										<span class="text-gray-600">Dinamis (wajib diisi)</span>
									</div>
									<div class="flex items-center gap-2 text-xs">
										<span class="w-4 h-4 rounded" style="background-color: #FFF9C4;"></span>
										<span class="text-gray-600">Editable (perlu diubah)</span>
									</div>
									<div class="flex items-center gap-2 text-xs">
										<span class="w-4 h-4 rounded border border-gray-200" style="background-color: transparent;"></span>
										<span class="text-gray-600 italic">Instruksi (catatan)</span>
									</div>
								</div>
							</div>

							{#if templateVariables.length > 0}
								<h4 class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
									Variabel ({templateVariables.length})
								</h4>
								<div class="space-y-2 max-h-96 overflow-y-auto">
									{#each templateVariables as variable}
										<div class="p-2 rounded border border-gray-100 text-xs" style="background-color: {getVariableColor(variable.type)}20;">
											<div class="flex items-center gap-1.5">
												<span class="w-2.5 h-2.5 rounded-full flex-shrink-0" style="background-color: {getVariableColor(variable.type)};"></span>
												<span class="font-medium text-gray-800 truncate">{variable.name || variable.full_text}</span>
											</div>
											<p class="text-gray-500 mt-0.5 ml-4">{getVariableLabel(variable.type)}</p>
										</div>
									{/each}
								</div>
							{:else}
								<p class="text-xs text-gray-500">Tidak ada variabel terdeteksi.</p>
							{/if}
						</div>
					{:else}
						<div class="card text-center py-8">
							<svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-gray-300 mx-auto mb-3" viewBox="0 0 20 20" fill="currentColor">
								<path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
							</svg>
							<p class="text-sm text-gray-500">Pilih template dari Dashboard untuk memulai.</p>
							<a href="/" class="btn-primary inline-block mt-3 text-sm">
								Ke Dashboard
							</a>
						</div>
					{/if}
				</div>
			</div>

			<!-- Right Panel: Editor -->
			<div class="lg:col-span-9 relative">
				{#if templateLoading}
					<div class="absolute inset-0 bg-white/70 z-10 flex items-center justify-center rounded-lg">
						<div class="flex flex-col items-center gap-3">
							<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
							<span class="text-gray-600 text-sm">Memuat template...</span>
						</div>
					</div>
				{/if}
				<TipTapEditor />
			</div>
		</div>
	{:else}
		<!-- Generate AI Mode -->
		<div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
			<!-- Left Panel: AI Generate Form -->
			<div class="lg:col-span-4 print:hidden">
				<div class="sticky top-4 space-y-4">
					<div class="card">
						<h3 class="font-semibold text-gray-900 mb-3">Generate dengan AI</h3>
						<p class="text-sm text-gray-500 mb-4">Deskripsikan kontrak yang ingin dibuat, isi variabel dasar, dan upload contoh dokumen (opsional).</p>

						<div class="space-y-3">
							<!-- Deskripsi Kebutuhan -->
							<div>
								<label for="ai-description" class="block text-sm font-medium text-gray-700 mb-1">
									Deskripsi Kebutuhan
								</label>
								<textarea
									id="ai-description"
									class="input-field min-h-[100px] resize-y"
									placeholder="Jelaskan jenis kontrak yang Anda butuhkan..."
									bind:value={aiDescription}
									disabled={aiGenerating}
								></textarea>
							</div>

							<!-- Variable Inputs -->
							<div>
								<label for="ai-nama-pihak-1" class="block text-sm font-medium text-gray-700 mb-1">
									Nama Pihak 1
								</label>
								<input
									id="ai-nama-pihak-1"
									type="text"
									class="input-field"
									placeholder="PT. Contoh Utama"
									bind:value={aiNamaPihak1}
									disabled={aiGenerating}
								/>
							</div>

							<div>
								<label for="ai-nama-pihak-2" class="block text-sm font-medium text-gray-700 mb-1">
									Nama Pihak 2
								</label>
								<input
									id="ai-nama-pihak-2"
									type="text"
									class="input-field"
									placeholder="CV. Mitra Sejahtera"
									bind:value={aiNamaPihak2}
									disabled={aiGenerating}
								/>
							</div>

							<div>
								<label for="ai-nomor-kontrak" class="block text-sm font-medium text-gray-700 mb-1">
									Nomor Kontrak
								</label>
								<input
									id="ai-nomor-kontrak"
									type="text"
									class="input-field"
									placeholder="001/KTR/2024"
									bind:value={aiNomorKontrak}
									disabled={aiGenerating}
								/>
							</div>

							<div>
								<label for="ai-tanggal" class="block text-sm font-medium text-gray-700 mb-1">
									Tanggal
								</label>
								<input
									id="ai-tanggal"
									type="text"
									class="input-field"
									placeholder="1 Januari 2024"
									bind:value={aiTanggal}
									disabled={aiGenerating}
								/>
							</div>

							<div>
								<label for="ai-nilai-kontrak" class="block text-sm font-medium text-gray-700 mb-1">
									Nilai Kontrak
								</label>
								<input
									id="ai-nilai-kontrak"
									type="text"
									class="input-field"
									placeholder="Rp 100.000.000"
									bind:value={aiNilaiKontrak}
									disabled={aiGenerating}
								/>
							</div>

							<!-- File Upload -->
							<div>
								<label for="ai-file" class="block text-sm font-medium text-gray-700 mb-1">
									Upload Contoh Dokumen (opsional)
								</label>
								<input
									id="ai-file"
									type="file"
									accept=".docx"
									class="input-field text-sm file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary hover:file:bg-primary-100"
									onchange={handleFileChange}
									disabled={aiGenerating}
								/>
								<p class="text-xs text-gray-400 mt-1">Upload contoh dokumen .docx sebagai referensi AI.</p>
							</div>

							<!-- Generate Button -->
							<button
								class="btn-primary w-full flex items-center justify-center gap-2 py-2.5"
								onclick={handleAiGenerate}
								disabled={aiGenerating || !aiDescription.trim()}
							>
								{#if aiGenerating}
									<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
									<span>Generating...</span>
								{:else}
									<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
										<path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z" />
									</svg>
									<span>Generate dengan AI</span>
								{/if}
							</button>
						</div>
					</div>
				</div>
			</div>

			<!-- Right Panel: Editor -->
			<div class="lg:col-span-8 relative">
				{#if aiGenerating}
					<div class="absolute inset-0 bg-white/70 z-10 flex items-center justify-center rounded-lg">
						<div class="flex flex-col items-center gap-3">
							<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
							<span class="text-gray-600 text-sm">Generating draft...</span>
						</div>
					</div>
				{/if}
				<TipTapEditor />
			</div>
		</div>
	{/if}
</div>
