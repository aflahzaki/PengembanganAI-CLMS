<script lang="ts">
	import ContractForm from '$lib/components/ContractForm.svelte';
	import TipTapEditor from '$lib/components/TipTapEditor.svelte';
	import ExportButton from '$lib/components/ExportButton.svelte';
</script>

<svelte:head>
	<title>Buat Draft Kontrak - CLMS</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<!-- Page Header -->
	<div class="mb-6 flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-gray-900">Buat Draft Kontrak</h1>
			<p class="mt-1 text-gray-600">Isi data dan generate draft kontrak secara otomatis</p>
		</div>
		<ExportButton />
	</div>

	<!-- Main Content Grid -->
	<div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
		<!-- Left Panel: Form -->
		<div class="lg:col-span-4">
			<div class="sticky top-4">
				<ContractForm />
			</div>
		</div>

		<!-- Right Panel: Editor -->
		<div class="lg:col-span-8">
			<TipTapEditor />
		</div>
	</div>
</div>
