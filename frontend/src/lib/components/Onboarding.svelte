<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';

	let visible = $state(false);
	let currentStep = $state(0);

	const steps = [
		{
			icon: 'document',
			title: 'Selamat datang di CLMS',
			description: 'Sistem pembuatan kontrak otomatis untuk PLN'
		},
		{
			icon: 'template',
			title: 'Pilih Template',
			description: 'Pilih dari 8 template kontrak resmi PLN atau upload sendiri'
		},
		{
			icon: 'ai',
			title: 'Generate dengan AI',
			description: 'Buat kontrak baru dengan bantuan AI berdasarkan kebutuhan Anda'
		}
	];

	onMount(() => {
		if (browser) {
			const done = localStorage.getItem('clms_onboarding_done');
			if (!done) {
				visible = true;
			}
		}
	});

	function next() {
		if (currentStep < steps.length - 1) {
			currentStep++;
		} else {
			finish();
		}
	}

	function skip() {
		finish();
	}

	function finish() {
		if (browser) {
			localStorage.setItem('clms_onboarding_done', 'true');
		}
		visible = false;
	}
</script>

{#if visible}
	<div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
		<div class="relative bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-8">
			<!-- Skip button -->
			<button
				onclick={skip}
				class="absolute top-4 right-4 text-xs text-gray-400 hover:text-gray-600 transition-colors"
			>
				Skip
			</button>

			<!-- Step content -->
			<div class="flex flex-col items-center text-center">
				<!-- Icon -->
				<div class="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mb-6">
					{#if steps[currentStep].icon === 'document'}
						<svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-primary" viewBox="0 0 20 20" fill="currentColor">
							<path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
						</svg>
					{:else if steps[currentStep].icon === 'template'}
						<svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-primary" viewBox="0 0 20 20" fill="currentColor">
							<path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
						</svg>
					{:else if steps[currentStep].icon === 'ai'}
						<svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-primary" viewBox="0 0 20 20" fill="currentColor">
							<path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" />
						</svg>
					{/if}
				</div>

				<!-- Title -->
				<h2 class="text-xl font-bold text-gray-800 mb-2">
					{steps[currentStep].title}
				</h2>

				<!-- Description -->
				<p class="text-gray-500 text-sm mb-8">
					{steps[currentStep].description}
				</p>

				<!-- Step indicators -->
				<div class="flex gap-2 mb-6">
					{#each steps as _, i}
						<div class="w-2 h-2 rounded-full transition-colors duration-200 {i === currentStep ? 'bg-primary' : 'bg-gray-200'}"></div>
					{/each}
				</div>

				<!-- Action button -->
				<button
					onclick={next}
					class="w-full py-3 px-6 bg-primary text-white font-medium rounded-lg hover:bg-primary/90 transition-colors duration-150"
				>
					{currentStep < steps.length - 1 ? 'Selanjutnya' : 'Mulai'}
				</button>
			</div>
		</div>
	</div>
{/if}
