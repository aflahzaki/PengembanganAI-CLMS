<script lang="ts">
	import { onMount } from 'svelte';
	import { includeOptional } from '$lib/stores/contract';

	let optionalEnabled = $state(true);

	onMount(() => {
		const unsub = includeOptional.subscribe((v) => { optionalEnabled = v; });
		return unsub;
	});

	function toggle() {
		includeOptional.update((v) => !v);
	}
</script>

<div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
	<div>
		<h4 class="font-medium text-gray-700">Klausul Opsional</h4>
		<p class="text-sm text-gray-500">Sertakan klausul opsional dalam draft kontrak</p>
	</div>
	<button
		type="button"
		role="switch"
		aria-checked={optionalEnabled}
		aria-label="Toggle klausul opsional"
		onclick={toggle}
		class="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 {optionalEnabled ? 'bg-primary' : 'bg-gray-300'}"
	>
		<span
			class="pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out {optionalEnabled ? 'translate-x-5' : 'translate-x-0'}"
		></span>
	</button>
</div>
