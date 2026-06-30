# Arsitektur CLMS

## Overview

```
┌─────────────────────────────────────────────────────────┐
│                     USER (Browser)                        │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP
┌─────────────────────┴───────────────────────────────────┐
│                  FRONTEND (SvelteKit)                     │
│  Port 5173 (dev) / 3000 (prod)                          │
│  - Dashboard (template library)                          │
│  - Draft Page (2 mode: template / AI)                   │
│  - TipTap Editor (rich text)                            │
│  - Export DOCX                                          │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API
┌─────────────────────┴───────────────────────────────────┐
│                  BACKEND (FastAPI)                        │
│  Port 8000                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Templates  │  │   Drafting   │  │    Export     │  │
│  │  API        │  │   Service    │  │   Service     │  │
│  └──────┬──────┘  └──────┬───────┘  └──────────────┘  │
│         │                 │                              │
│  ┌──────┴──────┐  ┌──────┴───────┐                     │
│  │  ChromaDB   │  │   Groq API   │                     │
│  │  (Vector DB)│  │   (LLM)      │                     │
│  └─────────────┘  └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Teknologi | Versi |
|-------|-----------|-------|
| Frontend | SvelteKit + TipTap | Svelte 5 |
| Backend | FastAPI (Python) | 0.104 |
| Database | ChromaDB | 0.4.22 |
| AI/LLM | Groq (Llama 3.3 70B) | Free tier |
| Export | python-docx | 1.1.0 |
| Deployment | Docker + docker-compose | - |

## API Endpoints

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | /health | Status server |
| GET | /api/templates | List template ChromaDB |
| GET | /api/templates/{slug} | Detail template |
| GET | /api/templates/docx | List template DOCX |
| GET | /api/templates/docx/{id}/html | HTML template |
| POST | /api/templates/docx/upload | Upload template baru |
| DELETE | /api/templates/docx/{id} | Hapus template |
| POST | /api/draft | Generate draft (ChromaDB) |
| POST | /api/draft/ai-generate | Generate dengan AI |
| POST | /api/export/docx | Export ke Word |
| POST | /api/upload/image | Upload gambar/TTD |

## Deployment

```bash
# Development
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev

# Production (Docker)
docker-compose up -d
```
