<script lang="ts">
	import type { DocxTemplateInfo } from '$lib/api/client';

	let { template, onUse, onDelete, onPreview }: {
		template: DocxTemplateInfo;
		onUse: (template: DocxTemplateInfo) => void;
		onDelete: (template: DocxTemplateInfo) => void;
		onPreview: (template: DocxTemplateInfo) => void;
	} = $props();

	function formatFileSize(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}
</script>

<div class="card flex flex-col justify-between h-full">
	<div>
		<div class="flex items-start justify-between mb-3">
			<div class="flex items-center gap-2">
				<div class="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center flex-shrink-0">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
					</svg>
				</div>
				<h3 class="font-semibold text-gray-900 text-sm leading-tight">{template.name}</h3>
			</div>
		</div>

		<div class="flex flex-wrap gap-2 mb-4">
			<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
				{template.variable_count} variabel
			</span>
			<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
				{formatFileSize(template.file_size_bytes)}
			</span>
		</div>
	</div>

	<div class="flex gap-2 mt-auto">
		<button
			class="btn-primary flex-1 text-sm py-2"
			onclick={() => onUse(template)}
		>
			Gunakan
		</button>
		<button
			class="btn-secondary text-sm py-2 px-3"
			onclick={() => onPreview(template)}
			title="Preview template"
		>
			<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
				<path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
				<path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd" />
			</svg>
		</button>
		<button
			class="btn-secondary text-sm py-2 px-3 !text-red-600 !border-red-300 hover:!bg-red-50"
			onclick={() => onDelete(template)}
			title="Hapus template"
		>
			<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
				<path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
			</svg>
		</button>
	</div>
</div>
