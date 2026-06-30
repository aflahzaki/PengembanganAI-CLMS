<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Editor, Mark, mergeAttributes } from '@tiptap/core';
	import StarterKit from '@tiptap/starter-kit';
	import Highlight from '@tiptap/extension-highlight';
	import Image from '@tiptap/extension-image';
	import { editorContent } from '$lib/stores/contract';
	import { uploadImage as apiUploadImage } from '$lib/api/client';

	let element: HTMLDivElement | undefined = $state();
	let editor: Editor | undefined = $state();
	let hasContent = $state(false);

	/**
	 * Custom mark extension to preserve inline-styled <mark> elements from backend HTML.
	 * The backend sends variable highlights as <mark style="background-color: #FFEB3B"> etc.
	 */
	const InlineStyledMark = Mark.create({
		name: 'inlineStyledMark',
		parseHTML() {
			return [
				{
					tag: 'mark',
					getAttrs: (node) => {
						const el = node as HTMLElement;
						const style = el.getAttribute('style');
						if (style) return { style };
						return false;
					}
				}
			];
		},
		addAttributes() {
			return {
				style: {
					default: null,
					parseHTML: (element) => element.getAttribute('style'),
					renderHTML: (attributes) => {
						if (!attributes.style) return {};
						return { style: attributes.style };
					}
				}
			};
		},
		renderHTML({ HTMLAttributes }) {
			return ['mark', mergeAttributes(HTMLAttributes), 0];
		}
	});

	/**
	 * Custom mark extension to preserve inline-styled <span> elements (for instruction variables).
	 */
	const InlineStyledSpan = Mark.create({
		name: 'inlineStyledSpan',
		parseHTML() {
			return [
				{
					tag: 'span',
					getAttrs: (node) => {
						const el = node as HTMLElement;
						const style = el.getAttribute('style');
						if (style) return { style };
						return false;
					}
				}
			];
		},
		addAttributes() {
			return {
				style: {
					default: null,
					parseHTML: (element) => element.getAttribute('style'),
					renderHTML: (attributes) => {
						if (!attributes.style) return {};
						return { style: attributes.style };
					}
				}
			};
		},
		renderHTML({ HTMLAttributes }) {
			return ['span', mergeAttributes(HTMLAttributes), 0];
		}
	});

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
				Highlight.configure({ multicolor: true }),
				InlineStyledMark,
				InlineStyledSpan,
				Image.configure({ inline: true, allowBase64: true })
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

	function insertImage() {
		const input = document.createElement('input');
		input.type = 'file';
		input.accept = 'image/png,image/jpeg';
		input.onchange = async () => {
			const file = input.files?.[0];
			if (!file || !editor) return;
			try {
				const { url } = await apiUploadImage(file);
				editor.chain().focus().setImage({ src: url }).run();
			} catch (err) {
				console.error('Failed to upload image:', err);
			}
		};
		input.click();
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

			<div class="w-px h-6 bg-gray-200 mx-1"></div>

			<button
				type="button"
				onclick={insertImage}
				class="p-1.5 rounded hover:bg-gray-100 text-gray-600"
				title="Insert Gambar/TTD"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
					<path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd" />
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
		padding: 1.5rem 2rem;
		min-height: 300px;
		outline: none;
		font-family: 'Times New Roman', Times, serif;
		font-size: 12pt;
		line-height: 1.6;
	}

	/* Contract document wrapper */
	.tiptap-editor :global(.contract-document) {
		max-width: 800px;
		margin: 0 auto;
	}

	/* Contract title - centered, larger font */
	.tiptap-editor :global(.ProseMirror h1) {
		text-align: center;
		font-size: 18px;
		font-weight: bold;
		margin-bottom: 24px;
		margin-top: 0;
	}

	/* Pasal section headings */
	.tiptap-editor :global(.ProseMirror h2) {
		font-size: 14px;
		font-weight: bold;
		margin-top: 24px;
		margin-bottom: 12px;
	}

	/* Sub-section headings */
	.tiptap-editor :global(.ProseMirror h3) {
		font-size: 13px;
		font-weight: bold;
		margin-top: 16px;
		margin-bottom: 8px;
	}

	/* Paragraphs - justified with proper spacing */
	.tiptap-editor :global(.ProseMirror p) {
		margin-bottom: 12px;
		line-height: 1.6;
		text-align: justify;
	}

	/* Ordered lists - main numbering */
	.tiptap-editor :global(.ProseMirror ol) {
		padding-left: 20px;
		margin-bottom: 12px;
	}

	/* Nested ordered lists - sub-items */
	.tiptap-editor :global(.ProseMirror ol ol) {
		margin-left: 20px;
		padding-left: 20px;
		margin-top: 4px;
		margin-bottom: 4px;
		list-style-type: lower-alpha;
	}

	/* Deep nested ordered lists */
	.tiptap-editor :global(.ProseMirror ol ol ol) {
		margin-left: 20px;
		list-style-type: decimal;
	}

	/* List items */
	.tiptap-editor :global(.ProseMirror li) {
		margin-bottom: 8px;
		line-height: 1.6;
		text-align: justify;
	}

	/* Nested list items - tighter spacing */
	.tiptap-editor :global(.ProseMirror ol ol li) {
		margin-bottom: 4px;
	}

	/* Pasal separator */
	.tiptap-editor :global(.ProseMirror hr) {
		border: none;
		border-top: 1px solid #e0e0e0;
		margin: 20px 0;
	}

	/* Pasal separator with specific class */
	.tiptap-editor :global(.ProseMirror hr.pasal-separator) {
		border: none;
		border-top: 1px solid #e0e0e0;
		margin: 20px 0;
	}

	/* Unordered lists */
	.tiptap-editor :global(.ProseMirror ul) {
		padding-left: 20px;
		margin-bottom: 12px;
	}

	.tiptap-editor :global(.ProseMirror ul li) {
		margin-bottom: 4px;
		line-height: 1.6;
	}

	/* Image styles */
	.tiptap-editor :global(.ProseMirror img) {
		max-width: 100%;
		height: auto;
		cursor: pointer;
		border: 2px solid transparent;
		border-radius: 4px;
		transition: border-color 0.2s;
	}

	.tiptap-editor :global(.ProseMirror img:hover) {
		border-color: #3b82f6;
	}

	.tiptap-editor :global(.ProseMirror img.ProseMirror-selectednode) {
		border-color: #3b82f6;
		outline: none;
	}

	/* Signing section styles */
	.tiptap-editor :global(.signing-section) {
		margin-top: 40px;
	}

	.tiptap-editor :global(.signature-placeholder) {
		height: 80px;
		border: 1px dashed #ccc;
		margin: 20px 0;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #999;
		cursor: pointer;
	}
</style>
