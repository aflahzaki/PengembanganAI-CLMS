<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Editor } from '@tiptap/core';
	import StarterKit from '@tiptap/starter-kit';
	import Highlight from '@tiptap/extension-highlight';
	import { editorContent } from '$lib/stores/contract';

	let element: HTMLDivElement | undefined = $state();
	let editor: Editor | undefined = $state();
	let hasContent = $state(false);

	onMount(() => {
		const unsub = editorContent.subscribe((content) => {
			if (editor && content && content !== editor.getHTML()) {
				editor.commands.setContent(content);
				hasContent = content.length > 0;
			} else if (!content) {
				hasContent = false;
			}
		});

		editor = new Editor({
			element: element!,
			extensions: [
				StarterKit,
				Highlight.configure({ multicolor: true })
			],
			content: '',
			onTransaction: () => {
				// Force Svelte reactivity
				editor = editor;
			},
			onUpdate: ({ editor: ed }) => {
				const html = ed.getHTML();
				editorContent.set(html);
				hasContent = html.length > 0 && html !== '<p></p>';
			}
		});

		return () => {
			unsub();
		};
	});

	onDestroy(() => {
		if (editor) {
			editor.destroy();
		}
	});

	function toggleBold() {
		editor?.chain().focus().toggleBold().run();
	}

	function toggleItalic() {
		editor?.chain().focus().toggleItalic().run();
	}

	function toggleHeading(level: 1 | 2 | 3) {
		editor?.chain().focus().toggleHeading({ level }).run();
	}

	function toggleBulletList() {
		editor?.chain().focus().toggleBulletList().run();
	}

	function toggleOrderedList() {
		editor?.chain().focus().toggleOrderedList().run();
	}

	function undo() {
		editor?.chain().focus().undo().run();
	}

	function redo() {
		editor?.chain().focus().redo().run();
	}
</script>

<div class="card p-0 overflow-hidden">
	<div class="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-gray-50">
		<h3 class="font-medium text-gray-700">Editor Kontrak</h3>
		{#if hasContent}
			<span class="text-xs text-green-600 bg-green-50 px-2 py-1 rounded-full">
				Konten tersedia
			</span>
		{/if}
	</div>

	<!-- Toolbar -->
	{#if editor}
		<div class="flex flex-wrap items-center gap-1 px-4 py-2 border-b border-gray-100 bg-white">
			<button
				type="button"
				onclick={undo}
				class="p-1.5 rounded hover:bg-gray-100 text-gray-600"
				title="Undo"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M7.707 3.293a1 1 0 010 1.414L5.414 7H11a7 7 0 017 7v2a1 1 0 11-2 0v-2a5 5 0 00-5-5H5.414l2.293 2.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
				</svg>
			</button>
			<button
				type="button"
				onclick={redo}
				class="p-1.5 rounded hover:bg-gray-100 text-gray-600"
				title="Redo"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M12.293 3.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 9H9a5 5 0 00-5 5v2a1 1 0 11-2 0v-2a7 7 0 017-7h5.586l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd" />
				</svg>
			</button>

			<div class="w-px h-6 bg-gray-200 mx-1"></div>

			<button
				type="button"
				onclick={toggleBold}
				class="p-1.5 rounded hover:bg-gray-100 font-bold text-gray-600 {editor.isActive('bold') ? 'bg-primary-50 text-primary' : ''}"
				title="Bold"
			>
				B
			</button>
			<button
				type="button"
				onclick={toggleItalic}
				class="p-1.5 rounded hover:bg-gray-100 italic text-gray-600 {editor.isActive('italic') ? 'bg-primary-50 text-primary' : ''}"
				title="Italic"
			>
				I
			</button>

			<div class="w-px h-6 bg-gray-200 mx-1"></div>

			<button
				type="button"
				onclick={() => toggleHeading(1)}
				class="p-1.5 rounded hover:bg-gray-100 text-xs font-bold text-gray-600 {editor.isActive('heading', { level: 1 }) ? 'bg-primary-50 text-primary' : ''}"
				title="Heading 1"
			>
				H1
			</button>
			<button
				type="button"
				onclick={() => toggleHeading(2)}
				class="p-1.5 rounded hover:bg-gray-100 text-xs font-bold text-gray-600 {editor.isActive('heading', { level: 2 }) ? 'bg-primary-50 text-primary' : ''}"
				title="Heading 2"
			>
				H2
			</button>
			<button
				type="button"
				onclick={() => toggleHeading(3)}
				class="p-1.5 rounded hover:bg-gray-100 text-xs font-bold text-gray-600 {editor.isActive('heading', { level: 3 }) ? 'bg-primary-50 text-primary' : ''}"
				title="Heading 3"
			>
				H3
			</button>

			<div class="w-px h-6 bg-gray-200 mx-1"></div>

			<button
				type="button"
				onclick={toggleBulletList}
				class="p-1.5 rounded hover:bg-gray-100 text-gray-600 {editor.isActive('bulletList') ? 'bg-primary-50 text-primary' : ''}"
				title="Bullet List"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M4 4a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zm0 4a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zm0 4a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zm0 4a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1z" clip-rule="evenodd" />
				</svg>
			</button>
			<button
				type="button"
				onclick={toggleOrderedList}
				class="p-1.5 rounded hover:bg-gray-100 text-gray-600 {editor.isActive('orderedList') ? 'bg-primary-50 text-primary' : ''}"
				title="Ordered List"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
					<path d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3 4a1 1 0 011-1h9a1 1 0 110 2H7a1 1 0 01-1-1zm0 4a1 1 0 011-1h9a1 1 0 110 2H7a1 1 0 01-1-1zm-3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" />
				</svg>
			</button>
		</div>
	{/if}

	<!-- Editor Content -->
	<div class="tiptap-editor" bind:this={element}></div>

	{#if !hasContent}
		<div class="px-4 py-8 text-center text-gray-400 border-t border-gray-100">
			<p>Belum ada konten. Klik "Generate Draft" untuk membuat draft kontrak.</p>
		</div>
	{/if}
</div>

<style>
	.tiptap-editor :global(mark.variable-highlight) {
		background-color: #FFEB3B;
		padding: 2px 4px;
		border-radius: 2px;
	}

	.tiptap-editor :global(mark) {
		background-color: #FFEB3B;
		padding: 2px 4px;
		border-radius: 2px;
	}

	.tiptap-editor :global(.ProseMirror) {
		padding: 1rem;
		min-height: 300px;
		outline: none;
	}

	.tiptap-editor :global(.ProseMirror p) {
		margin-bottom: 0.5rem;
	}
</style>
