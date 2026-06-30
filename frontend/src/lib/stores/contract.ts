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

// --- Auto-save to localStorage ---

const AUTOSAVE_KEY = 'clms_autosave';
const AUTOSAVE_DEBOUNCE_MS = 3000;

let autosaveTimer: ReturnType<typeof setTimeout> | null = null;

/**
 * Initialize autosave: subscribe to editorContent and debounce saves to localStorage.
 * Call this once on mount in the draft page.
 */
export function initAutosave(): () => void {
	const unsub = editorContent.subscribe((content) => {
		if (autosaveTimer) clearTimeout(autosaveTimer);
		autosaveTimer = setTimeout(() => {
			if (content && content !== '<p></p>' && content.length > 20) {
				try {
					localStorage.setItem(AUTOSAVE_KEY, content);
				} catch {
					// localStorage full or unavailable, ignore
				}
			}
		}, AUTOSAVE_DEBOUNCE_MS);
	});

	return () => {
		if (autosaveTimer) clearTimeout(autosaveTimer);
		unsub();
	};
}

/**
 * Get autosaved content from localStorage.
 */
export function getAutosave(): string | null {
	try {
		return localStorage.getItem(AUTOSAVE_KEY);
	} catch {
		return null;
	}
}

/**
 * Clear autosaved content from localStorage.
 */
export function clearAutosave(): void {
	try {
		localStorage.removeItem(AUTOSAVE_KEY);
	} catch {
		// ignore
	}
}

// --- Draft History (5 recent versions) ---

const HISTORY_KEY = 'clms_history';
const MAX_HISTORY = 5;

export interface HistoryEntry {
	timestamp: string;
	mode: 'template' | 'generate';
	templateName: string;
	htmlContent: string;
}

/**
 * Get draft history from localStorage.
 */
export function getHistory(): HistoryEntry[] {
	try {
		const raw = localStorage.getItem(HISTORY_KEY);
		if (!raw) return [];
		return JSON.parse(raw) as HistoryEntry[];
	} catch {
		return [];
	}
}

/**
 * Add a snapshot to draft history. FIFO, max 5 entries.
 * htmlContent stored is first 200 chars as preview.
 */
export function addToHistory(
	mode: 'template' | 'generate',
	templateName: string,
	fullHtml: string
): void {
	try {
		const history = getHistory();
		const entry: HistoryEntry = {
			timestamp: new Date().toISOString(),
			mode,
			templateName,
			htmlContent: fullHtml.substring(0, 200)
		};
		history.push(entry);
		// Keep only last 5
		while (history.length > MAX_HISTORY) {
			history.shift();
		}
		localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
	} catch {
		// ignore
	}
}

/**
 * Get the full HTML content for a history entry by loading from history.
 * Since we only store preview (200 chars), we store full content in a separate key.
 */
const HISTORY_FULL_KEY = 'clms_history_full';

export function addToHistoryFull(
	mode: 'template' | 'generate',
	templateName: string,
	fullHtml: string
): void {
	try {
		const history = getHistory();
		const fullHistory = getHistoryFull();

		const entry: HistoryEntry = {
			timestamp: new Date().toISOString(),
			mode,
			templateName,
			htmlContent: fullHtml.substring(0, 200)
		};
		history.push(entry);
		fullHistory.push(fullHtml);

		// Keep only last 5
		while (history.length > MAX_HISTORY) {
			history.shift();
			fullHistory.shift();
		}

		localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
		localStorage.setItem(HISTORY_FULL_KEY, JSON.stringify(fullHistory));
	} catch {
		// ignore
	}
}

export function getHistoryFull(): string[] {
	try {
		const raw = localStorage.getItem(HISTORY_FULL_KEY);
		if (!raw) return [];
		return JSON.parse(raw) as string[];
	} catch {
		return [];
	}
}
