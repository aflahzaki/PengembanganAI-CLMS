<script lang="ts">
	import { onMount } from 'svelte';
	import { getTemplates, generateDraft } from '$lib/api/client';
	import type { TemplateInfo } from '$lib/api/client';
	import {
		templates,
		selectedTemplate,
		variableValues,
		includeOptional,
		draftResponse,
		editorContent,
		isLoading,
		documentName,
		showError,
		showSuccess
	} from '$lib/stores/contract';
	import ClauseToggle from './ClauseToggle.svelte';

	let loadingTemplates = $state(false);
	let currentTemplate: TemplateInfo | null = $state(null);
	let currentVars: Record<string, string> = $state({});
	let loading = $state(false);
	let docName = $state('');

	onMount(() => {
		const unsub1 = selectedTemplate.subscribe((v) => { currentTemplate = v; });
		const unsub2 = variableValues.subscribe((v) => { currentVars = v; });
		const unsub3 = isLoading.subscribe((v) => { loading = v; });
		const unsub4 = documentName.subscribe((v) => { docName = v; });
		return () => { unsub1(); unsub2(); unsub3(); unsub4(); };
	});

	onMount(async () => {
		loadingTemplates = true;
		try {
			const data = await getTemplates();
			templates.set(data);
			if (data.length > 0) {
				selectedTemplate.set(data[0]);
				// Initialize variable values
				const vars: Record<string, string> = {};
				for (const v of data[0].variables) {
					vars[v.name] = v.default_value || '';
				}
				variableValues.set(vars);
			}
		} catch (err) {
			showError('Gagal memuat template. Pastikan backend berjalan di port 8000.');
		} finally {
			loadingTemplates = false;
		}
	});

	function handleVariableChange(name: string, value: string) {
		variableValues.update((vars) => ({ ...vars, [name]: value }));
	}

	function handleDocNameChange(value: string) {
		documentName.set(value);
	}

	async function handleGenerate() {
		if (!currentTemplate) {
			showError('Pilih template terlebih dahulu.');
			return;
		}

		let optionalFlag = true;
		includeOptional.subscribe((v) => { optionalFlag = v; })();

		isLoading.set(true);
		try {
			const vars = { ...currentVars };
			if (docName && docName.trim()) {
				vars['_document_name'] = docName.trim();
			}
			const result = await generateDraft({
				template_name: currentTemplate.name,
				variables: vars,
				include_optional: optionalFlag
			});
			draftResponse.set(result);
			editorContent.set(result.html_content);
			showSuccess('Draft kontrak berhasil dibuat!');
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : 'Gagal membuat draft kontrak.';
			showError(message);
		} finally {
			isLoading.set(false);
		}
	}
</script>

<div class="card">
	<h2 class="text-xl font-semibold text-primary mb-4">Form Draft Kontrak</h2>

	{#if loadingTemplates}
		<div class="flex items-center justify-center py-8">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
			<span class="ml-3 text-gray-600">Memuat template...</span>
		</div>
	{:else if currentTemplate}
		<div class="space-y-4">
			<!-- Template Info -->
			<div class="bg-primary-50 rounded-lg p-4 border border-primary-100">
				<h3 class="font-medium text-primary">{currentTemplate.name}</h3>
				<p class="text-sm text-gray-600 mt-1">{currentTemplate.description}</p>
				<div class="flex gap-4 mt-2 text-xs text-gray-500">
					<span>{currentTemplate.clauses_count} klausul total</span>
					<span>{currentTemplate.mandatory_clauses} wajib</span>
					<span>{currentTemplate.optional_clauses} opsional</span>
				</div>
			</div>

			<!-- Variable Inputs -->
			<div class="space-y-3">
				<h3 class="font-medium text-gray-700">Nama Dokumen</h3>
				<div>
					<input
						id="document-name"
						type="text"
						class="input-field"
						placeholder="Contoh: Kontrak Pengadaan Material 2024"
						value={docName}
						oninput={(e) => handleDocNameChange((e.target as HTMLInputElement).value)}
					/>
					<p class="mt-1 text-xs text-gray-500">Opsional. Digunakan sebagai judul dokumen dan nama file saat export.</p>
				</div>
			</div>

			<!-- Variable Inputs -->
			<div class="space-y-3">
				<h3 class="font-medium text-gray-700">Isi Data Variabel</h3>
				{#each currentTemplate.variables as variable}
					<div>
						<label for="var-{variable.name}" class="block text-sm font-medium text-gray-700 mb-1">
							{variable.name}
							{#if variable.required}
								<span class="text-red-500">*</span>
							{/if}
						</label>
						<input
							id="var-{variable.name}"
							type="text"
							class="input-field"
							placeholder="Masukkan {variable.name}"
							value={currentVars[variable.name] || ''}
							oninput={(e) => handleVariableChange(variable.name, (e.target as HTMLInputElement).value)}
						/>
					</div>
				{/each}
			</div>

			<!-- Clause Toggle -->
			<ClauseToggle />

			<!-- Generate Button -->
			<button
				class="btn-primary w-full flex items-center justify-center gap-2 py-3"
				onclick={handleGenerate}
				disabled={loading}
			>
				{#if loading}
					<div class="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
					<span>Memproses...</span>
				{:else}
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clip-rule="evenodd" />
					</svg>
					<span>Generate Draft</span>
				{/if}
			</button>
		</div>
	{:else}
		<p class="text-gray-500 text-center py-4">Tidak ada template tersedia. Pastikan backend berjalan.</p>
	{/if}
</div>
