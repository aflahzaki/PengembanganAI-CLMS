<script lang="ts">
	import { onMount } from 'svelte';
	import { getHealth } from '$lib/api/client';

	let healthStatus = $state<{ status: string; version: string; chroma_db_status: string; templates_loaded: number } | null>(null);
	let healthError = $state(false);

	onMount(async () => {
		try {
			healthStatus = await getHealth();
		} catch {
			healthError = true;
		}
	});
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
					<h3 class="text-sm font-medium text-gray-500">Template Tersedia</h3>
					<p class="text-lg font-semibold text-primary">
						{healthStatus?.templates_loaded ?? '-'}
					</p>
				</div>
			</div>
			<p class="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
				KHS Material Ketenagalistrikan
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

	<!-- Info Section -->
	<div class="card">
		<h2 class="text-lg font-semibold text-gray-900 mb-4">Tentang CLMS</h2>
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<div>
				<h3 class="font-medium text-gray-700 mb-2">Fitur Utama</h3>
				<ul class="space-y-2 text-sm text-gray-600">
					<li class="flex items-start gap-2">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-primary mt-0.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
						</svg>
						<span>Pembuatan draft kontrak otomatis berbasis template</span>
					</li>
					<li class="flex items-start gap-2">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-primary mt-0.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
						</svg>
						<span>Editor dokumen real-time dengan formatting</span>
					</li>
					<li class="flex items-start gap-2">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-primary mt-0.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
						</svg>
						<span>Klausul opsional yang dapat dipilih sesuai kebutuhan</span>
					</li>
					<li class="flex items-start gap-2">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-primary mt-0.5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
						</svg>
						<span>Ekspor ke format DOCX (Microsoft Word)</span>
					</li>
				</ul>
			</div>
			<div>
				<h3 class="font-medium text-gray-700 mb-2">Cara Penggunaan</h3>
				<ol class="space-y-2 text-sm text-gray-600 list-decimal list-inside">
					<li>Buka halaman "Buat Draft Kontrak"</li>
					<li>Isi variabel yang diperlukan (nama pengadaan, nomor kontrak, dll)</li>
					<li>Pilih apakah klausul opsional akan disertakan</li>
					<li>Klik "Generate Draft" untuk membuat draft</li>
					<li>Edit draft menggunakan editor yang tersedia</li>
					<li>Ekspor ke DOCX untuk penggunaan lebih lanjut</li>
				</ol>
			</div>
		</div>
	</div>
</div>
