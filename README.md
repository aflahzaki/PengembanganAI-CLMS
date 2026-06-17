# CLMS - Contract Lifecycle Management System

Sistem manajemen siklus kontrak berbasis AI untuk otomatisasi pembuatan, pengelolaan, dan ekspor dokumen kontrak harga satuan ketenagalistrikan PLN.

## Deskripsi Proyek

CLMS adalah platform yang mengintegrasikan **Retrieval-Augmented Generation (RAG)** dengan template kontrak standar PLN untuk menghasilkan draft kontrak secara otomatis. Sistem ini mengekstrak klausul-klausul dari template Excel, menyimpannya dalam vector database (ChromaDB), dan menggunakan LLM lokal untuk menghasilkan kontrak yang lengkap dan akurat.

### Fitur Utama

- Parsing otomatis template kontrak dari Excel (45+ klausul dengan variabel)
- RAG pipeline dengan ChromaDB untuk pencarian klausul yang relevan
- Generasi draft kontrak menggunakan LLM lokal (LMStudio)
- Editor rich-text berbasis TipTap untuk review dan editing
- Ekspor ke format Microsoft Word (.docx) dengan formatting profesional
- Multi-template support (extensible untuk berbagai jenis kontrak)

## Arsitektur Sistem

```
+------------------------------------------------------------------+
|                         CLMS Architecture                          |
+------------------------------------------------------------------+
|                                                                    |
|   +------------------+         +----------------------------+     |
|   |    Frontend      |  HTTP   |         Backend            |     |
|   |  (SvelteKit +    | <-----> |       (FastAPI)            |     |
|   |   TipTap Editor) |   API   |                            |     |
|   +------------------+         +----------------------------+     |
|                                |                            |     |
|                                |  +---------------------+   |     |
|                                |  |    RAG Pipeline     |   |     |
|                                |  |                     |   |     |
|                                |  |  Excel Parser       |   |     |
|                                |  |       |             |   |     |
|                                |  |       v             |   |     |
|                                |  |  Embeddings         |   |     |
|                                |  |       |             |   |     |
|                                |  |       v             |   |     |
|                                |  |  ChromaDB           |   |     |
|                                |  |       |             |   |     |
|                                |  |       v             |   |     |
|                                |  |  Retriever          |   |     |
|                                |  +---------------------+   |     |
|                                |                            |     |
|                                |  +---------------------+   |     |
|                                |  |    Services         |   |     |
|                                |  |                     |   |     |
|                                |  |  LLM Service ----+  |   |     |
|                                |  |  Drafting Svc    |  |   |     |
|                                |  |  Export Service   |  |   |     |
|                                |  +---------------------+   |     |
|                                |            |               |     |
|                                +----------------------------+     |
|                                             |                     |
|                                             v                     |
|                                +----------------------------+     |
|                                |   LMStudio (Local LLM)    |     |
|                                |   localhost:1234           |     |
|                                +----------------------------+     |
|                                                                    |
+------------------------------------------------------------------+
```

## Tech Stack

| Layer | Teknologi | Keterangan |
|-------|-----------|------------|
| Frontend | SvelteKit | Framework web modern dengan SSR |
| Editor | TipTap | Rich-text editor berbasis ProseMirror |
| Backend | FastAPI | Python web framework async |
| Vector DB | ChromaDB | Embedded vector database |
| LLM | LMStudio | Local LLM server (Llama 3 8B) |
| Embeddings | all-MiniLM-L6-v2 | Sentence transformer untuk semantic search |
| Document | python-docx | Generasi file Microsoft Word |
| Data Source | OpenPyXL | Parsing template Excel |
| Validation | Pydantic | Data validation dan serialization |

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+ (untuk frontend)
- LMStudio (opsional, untuk fitur AI drafting)

### Backend Setup

```bash
# Clone repository
git clone <repo-url>
cd PengembanganAI-CLMS

# Setup backend
cd backend
pip install -r requirements.txt

# Copy environment config
cp .env.example .env

# Ingest template data ke ChromaDB
python scripts/ingest_templates.py

# Jalankan server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Dari root project
cd frontend

# Install dependencies
npm install

# Jalankan development server
npm run dev
```

### Integration Test (tanpa LLM)

```bash
cd backend
python scripts/test_integration.py
```

## API Documentation

### Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/health` | Health check status |
| GET | `/api/templates` | Daftar template tersedia |
| GET | `/api/templates/{name}` | Detail template spesifik |
| POST | `/api/draft` | Generate draft kontrak |
| POST | `/api/export/docx` | Export ke format Word |

### Contoh Request

#### Generate Draft

```bash
curl -X POST http://localhost:8000/api/draft \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "KHS Material Ketenagalistrikan",
    "variables": {
      "NAMA_PIHAK_1": "PT PLN (Persero)",
      "NAMA_PIHAK_2": "PT Supplier Listrik",
      "NOMOR_KONTRAK": "001/KHS/PLN/2024",
      "NILAI_KONTRAK": "Rp 1.000.000.000"
    },
    "include_optional": true
  }'
```

#### Export ke DOCX

```bash
curl -X POST http://localhost:8000/api/export/docx \
  -H "Content-Type: application/json" \
  -d '{
    "html_content": "<h1>KONTRAK HARGA SATUAN</h1><p>Isi kontrak...</p>",
    "format": "docx",
    "filename": "kontrak_001"
  }' --output kontrak_001.docx
```

## Screenshots

> *Screenshot akan ditambahkan setelah UI selesai*

| Halaman | Deskripsi |
|---------|-----------|
| Dashboard | Halaman utama dengan daftar kontrak |
| Editor | TipTap editor untuk edit draft kontrak |
| Export | Preview dan export ke Word |

## Project Structure

```
PengembanganAI-CLMS/
|-- backend/
|   |-- app/
|   |   |-- api/routes/      # FastAPI route handlers
|   |   |-- models/          # Pydantic schemas
|   |   |-- rag/             # RAG pipeline (embeddings, ingest, retriever)
|   |   |-- services/        # Business logic (drafting, export, LLM)
|   |   |-- utils/           # Utilities (Excel parser, text processing)
|   |   |-- config.py        # Application configuration
|   |   +-- main.py          # FastAPI application entry point
|   |-- data/
|   |   |-- chroma_db/       # ChromaDB persistent storage
|   |   +-- templates/       # Excel template files
|   |-- scripts/             # CLI scripts (ingestion, integration tests)
|   |-- tests/               # Pytest test suite
|   +-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- lib/             # Svelte components
|   |   +-- routes/          # SvelteKit pages
|   +-- package.json
+-- README.md
```

## Development Roadmap

| Phase | Status | Deskripsi |
|-------|--------|-----------|
| Phase 1 | Done | Backend RAG pipeline + Excel parsing |
| Phase 2 | Done | API endpoints + DOCX export |
| Phase 3 | Done | Frontend SvelteKit + TipTap editor |
| Phase 4 | In Progress | Enhanced export + multi-template support |
| Phase 5 | Planned | User authentication + role management |
| Phase 6 | Planned | Contract versioning + audit trail |
| Phase 7 | Planned | Approval workflow + digital signature |
| Phase 8 | Planned | Dashboard analytics + reporting |

## Template yang Didukung

| Template | Status | Deskripsi |
|----------|--------|-----------|
| KHS Material Ketenagalistrikan | Active | Kontrak Harga Satuan pengadaan material |
| KHS Jasa | Planned | Kontrak Harga Satuan untuk jasa |
| Kontrak Lump Sum | Planned | Kontrak nilai tetap |
| SPK | Planned | Surat Perintah Kerja |

## Testing

```bash
# Unit tests
cd backend
python3 -m pytest tests/ -v

# Integration tests (tanpa LLM)
python scripts/test_integration.py
```

## Tim Pengembang

| Role | Nama |
|------|------|
| Project Lead | - |
| Backend Developer | - |
| Frontend Developer | - |
| AI/ML Engineer | - |

## Lisensi

Proyek internal - Hak cipta dilindungi.

---

*Dokumentasi ini di-generate dan dipelihara sebagai bagian dari pengembangan CLMS.*
