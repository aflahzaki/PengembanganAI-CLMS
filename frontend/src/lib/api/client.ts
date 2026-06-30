/**
 * API client for FastAPI backend communication.
 * All endpoints proxy to localhost:8000 via Vite dev proxy.
 */

const BASE_URL = '/api';

export interface VariableSchema {
	name: string;
	description: string | null;
	required: boolean;
	default_value: string | null;
}

export interface ClauseSchema {
	pasal_number: string;
	section_name: string;
	clause_text: string;
	variables: string[];
	is_mandatory: boolean;
}

export interface TemplateInfo {
	name: string;
	description: string;
	clauses_count: number;
	variables: VariableSchema[];
	mandatory_clauses: number;
	optional_clauses: number;
}

export interface DraftRequest {
	template_name: string;
	variables: Record<string, string>;
	include_optional: boolean;
}

export interface DraftResponse {
	html_content: string;
	metadata: Record<string, unknown>;
	unfilled_variables: string[];
}

export interface ExportRequest {
	html_content: string;
	format: 'docx';
	filename?: string;
}

export interface HealthResponse {
	status: string;
	version: string;
	chroma_db_status: string;
	templates_loaded: number;
}

class ApiError extends Error {
	status: number;
	detail: string;

	constructor(status: number, detail: string) {
		super(detail);
		this.status = status;
		this.detail = detail;
		this.name = 'ApiError';
	}
}

async function handleResponse<T>(response: Response): Promise<T> {
	if (!response.ok) {
		let detail = `Request failed with status ${response.status}`;
		try {
			const errorBody = await response.json();
			detail = errorBody.detail || detail;
		} catch {
			// response body may not be JSON
		}
		throw new ApiError(response.status, detail);
	}
	// Handle 204 No Content responses that have no body
	if (response.status === 204) {
		return undefined as unknown as T;
	}
	return response.json();
}

/**
 * Check backend health status.
 */
export async function getHealth(): Promise<HealthResponse> {
	const response = await fetch('/health');
	return handleResponse<HealthResponse>(response);
}

/**
 * Fetch all available templates.
 */
export async function getTemplates(): Promise<TemplateInfo[]> {
	const response = await fetch(`${BASE_URL}/templates`);
	return handleResponse<TemplateInfo[]>(response);
}

/**
 * Fetch a specific template by name.
 */
export async function getTemplate(name: string): Promise<TemplateInfo> {
	const response = await fetch(`${BASE_URL}/templates/${encodeURIComponent(name)}`);
	return handleResponse<TemplateInfo>(response);
}

/**
 * Generate a contract draft.
 */
export async function generateDraft(request: DraftRequest): Promise<DraftResponse> {
	const response = await fetch(`${BASE_URL}/draft`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(request)
	});
	return handleResponse<DraftResponse>(response);
}

// =============================================
// DOCX Template Library API
// =============================================

export interface DocxVariableInfo {
	name: string;
	type: 'dynamic' | 'editable' | 'instruction';
	full_text: string;
}

export interface DocxTemplateInfo {
	id: string;
	name: string;
	filename: string;
	variable_count: number;
	variables: DocxVariableInfo[];
	file_size_bytes: number;
}

export interface DocxTemplateHtmlResponse {
	id: string;
	name: string;
	html_content: string;
	variables: DocxVariableInfo[];
}

/**
 * Fetch all DOCX templates.
 */
export async function getDocxTemplates(): Promise<DocxTemplateInfo[]> {
	const response = await fetch(`${BASE_URL}/templates/docx`);
	return handleResponse<DocxTemplateInfo[]>(response);
}

/**
 * Fetch a specific DOCX template's HTML content.
 */
export async function getDocxTemplateHtml(id: string): Promise<DocxTemplateHtmlResponse> {
	const response = await fetch(`${BASE_URL}/templates/docx/${encodeURIComponent(id)}/html`);
	return handleResponse<DocxTemplateHtmlResponse>(response);
}

/**
 * Upload a new DOCX template.
 */
export async function uploadDocxTemplate(file: File): Promise<DocxTemplateInfo> {
	const formData = new FormData();
	formData.append('file', file);
	const response = await fetch(`${BASE_URL}/templates/docx/upload`, {
		method: 'POST',
		body: formData
	});
	return handleResponse<DocxTemplateInfo>(response);
}

/**
 * Delete a DOCX template by ID.
 */
export async function deleteDocxTemplate(id: string): Promise<void> {
	const response = await fetch(`${BASE_URL}/templates/docx/${encodeURIComponent(id)}`, {
		method: 'DELETE'
	});
	await handleResponse<void>(response);
}

// =============================================
// AI Generate API
// =============================================

export interface AiGenerateResponse {
	html_content: string;
	metadata: Record<string, unknown>;
}

/**
 * Generate a contract draft using AI.
 * Sends description, variables, and optional reference DOCX file.
 */
export async function generateAiDraft(
	description: string,
	variables: Record<string, string>,
	referenceFile?: File
): Promise<AiGenerateResponse> {
	const formData = new FormData();
	formData.append('description', description);
	formData.append('variables', JSON.stringify(variables));
	if (referenceFile) {
		formData.append('reference_file', referenceFile);
	}
	const response = await fetch(`${BASE_URL}/draft/ai-generate`, {
		method: 'POST',
		body: formData
	});
	return handleResponse<AiGenerateResponse>(response);
}

/**
 * Upload an image file (png/jpg) and return the URL.
 */
export async function uploadImage(file: File): Promise<{ url: string }> {
	const formData = new FormData();
	formData.append('file', file);
	const response = await fetch(`${BASE_URL}/upload/image`, {
		method: 'POST',
		body: formData
	});
	return handleResponse<{ url: string }>(response);
}

/**
 * Export HTML content to DOCX and trigger file download.
 */
export async function exportToDocx(htmlContent: string, filename?: string): Promise<void> {
	const body: ExportRequest = {
		html_content: htmlContent,
		format: 'docx',
		filename: filename || 'kontrak_draft.docx'
	};

	const response = await fetch(`${BASE_URL}/export/docx`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});

	if (!response.ok) {
		let detail = `Export gagal dengan status ${response.status}`;
		try {
			const errorBody = await response.json();
			detail = errorBody.detail || detail;
		} catch {
			// response body is not JSON (it's a file)
		}
		throw new ApiError(response.status, detail);
	}

	// Trigger file download
	const blob = await response.blob();
	const url = window.URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename || 'kontrak_draft.docx';
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
	window.URL.revokeObjectURL(url);
}
