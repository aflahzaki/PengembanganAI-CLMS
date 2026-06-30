# Changelog - CLMS AI

## v1.0.0 (2024-06-30)

### Fitur Utama
- Template Library: 8 template kontrak PLN resmi (DOCX)
- 2 Mode: Dari Template (instant) dan Generate AI (Groq)
- TipTap rich-text editor dengan highlight variabel 3-tier
- Export ke Microsoft Word (DOCX) dengan format profesional
- Upload/hapus template DOCX
- Upload gambar tanda tangan (TTD)
- Dark mode
- Auto-save ke localStorage
- Keyboard shortcuts (Ctrl+S, Ctrl+Shift+G)
- Draft history (5 versi terakhir)
- Print-friendly view
- Responsive mobile
- Postman API collection

### Teknis
- Backend: FastAPI + ChromaDB + python-docx
- Frontend: SvelteKit (Svelte 5) + TailwindCSS + TipTap
- AI: Groq API (Llama 3.3 70B, gratis)
- Rate limiting: 60 req/min per IP
- Docker support: docker-compose.yml
- E2E test script
- Request logging middleware
- Error boundary frontend

### Keamanan
- Input validation (max variabel, max deskripsi length)
- File upload validation (magic bytes, size limit)
- Path traversal prevention
- Rate limiting (slowapi)
- CORS configured
