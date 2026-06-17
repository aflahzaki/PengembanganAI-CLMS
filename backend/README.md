# CLMS Backend - Contract Lifecycle Management System

RAG-powered backend for automated contract drafting, using templates from KHS (Kontrak Harga Satuan) for PLN material procurement.

## Architecture

```
backend/
├── app/
│   ├── api/           # FastAPI routes and dependencies
│   │   ├── routes/
│   │   │   ├── drafting.py    # POST /api/draft
│   │   │   ├── templates.py   # GET /api/templates
│   │   │   └── export.py      # POST /api/export/docx
│   │   └── dependencies.py    # DI container
│   ├── models/        # Pydantic schemas
│   ├── rag/           # RAG pipeline (embeddings, ingest, retriever, prompts)
│   ├── services/      # Business logic (LLM, drafting, export)
│   ├── utils/         # Utilities (Excel parser, text processing)
│   ├── config.py      # Application settings
│   └── main.py        # FastAPI app entry point
├── data/
│   ├── templates/     # Excel template files
│   └── chroma_db/     # ChromaDB persistent storage
├── scripts/
│   └── ingest_templates.py   # Template ingestion CLI
├── tests/             # Pytest test suite
├── requirements.txt   # Python dependencies
└── .env.example       # Environment variables template
```

## Setup

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your LMStudio endpoint URL
```

### 3. Ingest templates

```bash
python scripts/ingest_templates.py
```

### 4. Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /api/templates | List available templates |
| GET | /api/templates/{name} | Get template details |
| POST | /api/draft | Generate contract draft |
| POST | /api/export/docx | Export HTML to DOCX |

## Key Components

### RAG Pipeline

1. **Excel Parser** - Extracts clauses from the CLMS Pemetaan Kontrak Excel file
2. **Ingest Service** - Stores parsed clauses in ChromaDB with metadata
3. **Retriever Service** - Queries ChromaDB for relevant clauses
4. **LLM Service** - Calls LMStudio for AI-powered drafting

### LLM Integration

Uses LMStudio with an OpenAI-compatible API endpoint at `localhost:1234/v1`. The system prompts are tailored for Indonesian legal language and formal contract drafting.

### Output Formats

- **HTML** (primary) - Compatible with TipTap rich text editor
- **DOCX** (secondary) - Microsoft Word format via python-docx

## Testing

```bash
python -m pytest tests/ -v
```

## Technology Stack

- **FastAPI** - Web framework
- **ChromaDB** - Vector database (in-process, persistent)
- **LangChain** - LLM orchestration utilities
- **openpyxl** - Excel file parsing
- **python-docx** - DOCX generation
- **httpx** - Async HTTP client for LLM API calls
- **Pydantic** - Data validation and settings management
