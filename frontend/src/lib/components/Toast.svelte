<script lang="ts">
	import { onMount } from 'svelte';
	import { errorMessage, successMessage } from '$lib/stores/contract';

	let errorMsg = $state('');
	let successMsg = $state('');

	onMount(() => {
		const unsub1 = errorMessage.subscribe((v) => { errorMsg = v; });
		const unsub2 = successMessage.subscribe((v) => { successMsg = v; });
		return () => { unsub1(); unsub2(); };
	});

	function dismissError() {
		errorMessage.set('');
	}

	function dismissSuccess() {
		successMessage.set('');
	}
</script>

<!-- Error Toast -->
{#if errorMsg}
	<div class="fixed top-4 right-4 z-50 animate-slide-in">
		<div class="flex items-center gap-3 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg shadow-lg max-w-md">
			<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0 text-red-500" viewBox="0 0 20 20" fill="currentColor">
				<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
			</svg>
			<p class="text-sm flex-1">{errorMsg}</p>
			<button onclick={dismissError} class="text-red-400 hover:text-red-600" aria-label="Tutup">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
				</svg>
			</button>
		</div>
	</div>
{/if}

<!-- Success Toast -->
{#if successMsg}
	<div class="fixed top-4 right-4 z-50 animate-slide-in">
		<div class="flex items-center gap-3 bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg shadow-lg max-w-md">
			<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0 text-green-500" viewBox="0 0 20 20" fill="currentColor">
				<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
			</svg>
			<p class="text-sm flex-1">{successMsg}</p>
			<button onclick={dismissSuccess} class="text-green-400 hover:text-green-600" aria-label="Tutup">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
				</svg>
			</button>
		</div>
	</div>
{/if}

<style>
	@keyframes slide-in {
		from {
			transform: translateX(100%);
			opacity: 0;
		}
		to {
			transform: translateX(0);
			opacity: 1;
		}
	}

	:global(.animate-slide-in) {
		animation: slide-in 0.3s ease-out;
	}
</style>
