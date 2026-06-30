/**
 * Svelte stores for contract state management.
 * Uses Svelte 5 runes-compatible writable stores.
 */

import { writable } from 'svelte/store';
import type { TemplateInfo, DraftResponse, DocxTemplateInfo } from '$lib/api/client';

/** Currently selected template */
export const selectedTemplate = writable<TemplateInfo | null>(null);

/** All available templates */
export const templates = writable<TemplateInfo[]>([]);

/** Variable values filled in by user */
export const variableValues = writable<Record<string, string>>({});

/** Whether to include optional clauses */
export const includeOptional = writable<boolean>(true);

/** Generated draft response */
export const draftResponse = writable<DraftResponse | null>(null);

/** Current HTML content in the editor */
export const editorContent = writable<string>('');

/** Loading state */
export const isLoading = writable<boolean>(false);

/** Error message for toast notifications */
export const errorMessage = writable<string>('');

/** Success message for toast notifications */
export const successMessage = writable<string>('');

/** DOCX templates list */
export const docxTemplates = writable<DocxTemplateInfo[]>([]);

/** Currently selected DOCX template */
export const selectedDocxTemplate = writable<DocxTemplateInfo | null>(null);

/** Draft mode: 'template' or 'generate' */
export const draftMode = writable<'template' | 'generate'>('template');

/** Document name for dynamic export filename */
export const documentName = writable<string>('');

/**
 * Show error toast that auto-clears after delay.
 */
export function showError(message: string, duration = 5000): void {
	errorMessage.set(message);
	setTimeout(() => errorMessage.set(''), duration);
}

/**
 * Show success toast that auto-clears after delay.
 */
export function showSuccess(message: string, duration = 3000): void {
	successMessage.set(message);
	setTimeout(() => successMessage.set(''), duration);
}
