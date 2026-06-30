<script lang="ts">
	import '../app.css';
	import Toast from '$lib/components/Toast.svelte';
	import { page } from '$app/state';

	let { children } = $props();

	let mobileMenuOpen = $state(false);

	const navItems = [
		{ href: '/', label: 'Dashboard' },
		{ href: '/draft', label: 'Buat Draft Kontrak' }
	];

	function toggleMobileMenu() {
		mobileMenuOpen = !mobileMenuOpen;
	}

	function closeMobileMenu() {
		mobileMenuOpen = false;
	}
</script>

<div class="min-h-screen flex flex-col">
	<!-- Header -->
	<header class="bg-primary text-white shadow-lg print:hidden">
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
						<p class="text-xs text-white/70 hidden sm:block">Contract Lifecycle Management System</p>
					</div>
				</div>

				<!-- Desktop Nav -->
				<nav class="hidden md:flex items-center gap-1">
					{#each navItems as item}
						<a
							href={item.href}
							class="px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-150 {page.url.pathname === item.href ? 'bg-white/20 text-white' : 'text-white/80 hover:bg-white/10 hover:text-white'}"
						>
							{item.label}
						</a>
					{/each}
				</nav>

				<!-- Mobile Hamburger Button -->
				<button
					class="md:hidden p-2 rounded-lg hover:bg-white/10 transition-colors"
					onclick={toggleMobileMenu}
					aria-label="Toggle menu"
				>
					{#if mobileMenuOpen}
						<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					{:else}
						<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
						</svg>
					{/if}
				</button>
			</div>

			<!-- Mobile Nav Menu -->
			{#if mobileMenuOpen}
				<nav class="md:hidden pb-4 border-t border-white/10 pt-2">
					{#each navItems as item}
						<a
							href={item.href}
							class="block px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-150 {page.url.pathname === item.href ? 'bg-white/20 text-white' : 'text-white/80 hover:bg-white/10 hover:text-white'}"
							onclick={closeMobileMenu}
						>
							{item.label}
						</a>
					{/each}
				</nav>
			{/if}
		</div>
	</header>

	<!-- Main Content -->
	<main class="flex-1">
		{@render children()}
	</main>

	<!-- Footer -->
	<footer class="bg-white border-t border-gray-100 py-4 print:hidden">
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
		padding: 2px 4px;
		border-radius: 2px;
	}

	:global(.tiptap-editor mark[style]) {
		padding: 2px 4px;
		border-radius: 2px;
	}

	:global(.tiptap-editor span[style]) {
		/* Preserve inline styled spans for instruction variables */
	}
</style>
