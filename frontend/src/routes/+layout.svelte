<script lang="ts">
	import '../app.css';
	import Toast from '$lib/components/Toast.svelte';
	import { page } from '$app/state';

	let { children } = $props();

	const navItems = [
		{ href: '/', label: 'Dashboard' },
		{ href: '/draft', label: 'Buat Draft Kontrak' }
	];
</script>

<div class="min-h-screen flex flex-col">
	<!-- Header -->
	<header class="bg-primary text-white shadow-lg">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex items-center justify-between h-16">
				<div class="flex items-center gap-3">
					<div class="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
						</svg>
					</div>
					<div>
						<h1 class="text-lg font-bold tracking-tight">CLMS</h1>
						<p class="text-xs text-white/70">Contract Lifecycle Management System</p>
					</div>
				</div>

				<nav class="flex items-center gap-1">
					{#each navItems as item}
						<a
							href={item.href}
							class="px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-150 {page.url.pathname === item.href ? 'bg-white/20 text-white' : 'text-white/80 hover:bg-white/10 hover:text-white'}"
						>
							{item.label}
						</a>
					{/each}
				</nav>
			</div>
		</div>
	</header>

	<!-- Main Content -->
	<main class="flex-1">
		{@render children()}
	</main>

	<!-- Footer -->
	<footer class="bg-white border-t border-gray-100 py-4">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
			<p class="text-center text-sm text-gray-500">
				CLMS - Contract Lifecycle Management System &copy; 2024 PLN
			</p>
		</div>
	</footer>

	<!-- Toast Notifications -->
	<Toast />
</div>

<style>
	:global(mark.variable-highlight) {
		background-color: #FFEB3B;
		padding: 2px 4px;
		border-radius: 2px;
	}

	:global(.tiptap-editor mark) {
		background-color: #FFEB3B;
		padding: 2px 4px;
		border-radius: 2px;
	}
</style>
