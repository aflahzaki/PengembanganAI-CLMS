"""FastAPI application entry point for CLMS Backend.

Configures the application with CORS middleware, rate limiting,
lifespan events, and includes all API routers.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.routes import drafting, export, templates, docx_templates
from app.config import settings

logger = logging.getLogger(__name__)

# Rate limiter setup: 60 requests/minute per IP
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# OpenAPI tags metadata for organized Swagger docs
tags_metadata = [
    {"name": "health", "description": "Status dan kesehatan server"},
    {"name": "templates", "description": "Template kontrak dari ChromaDB"},
    {"name": "docx-templates", "description": "Template DOCX library"},
    {"name": "drafting", "description": "Generate draft kontrak"},
    {"name": "export", "description": "Export dokumen ke DOCX"},
    {"name": "upload", "description": "Upload file (gambar, template)"},
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events.

    On startup:
    - Initializes ChromaDB connection
    - Validates template availability

    On shutdown:
    - Cleans up resources
    """
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"ChromaDB path: {settings.chroma_db_absolute_path}")
    print(f"Templates dir: {settings.templates_absolute_path}")

    # Verify ChromaDB directory exists
    settings.chroma_db_absolute_path.mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    print("Shutting down CLMS Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Contract Lifecycle Management System Backend with RAG Pipeline. "
        "Provides contract template retrieval, AI-powered drafting, "
        "and document export capabilities."
    ),
    lifespan=lifespan,
    openapi_tags=tags_metadata,
)

# Attach rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
# No authentication required per project requirements, so credentials are disabled.
# Wildcard origins with allow_credentials=True is invalid per the CORS spec.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(drafting.router)
app.include_router(docx_templates.router)
app.include_router(templates.router)
app.include_router(export.router)


@app.get("/health", tags=["health"])
async def health_check(request: Request):
    """Detailed health check endpoint.

    Checks connectivity and status of all dependent services:
    - ChromaDB: connection and document count
    - LLM API: reachability check
    - DOCX Templates: count of available templates

    Returns:
        Dict with service status information.
    """
    services = {}

    # Check ChromaDB
    try:
        import chromadb

        client = chromadb.PersistentClient(
            path=str(settings.chroma_db_absolute_path)
        )
        collections = client.list_collections()
        total_documents = 0
        for collection in collections:
            total_documents += collection.count()
        services["chromadb"] = {
            "status": "connected",
            "documents": total_documents,
        }
    except Exception as e:
        logger.warning("ChromaDB health check failed: %s", e)
        services["chromadb"] = {
            "status": "error",
            "detail": str(e),
        }

    # Check LLM API reachability
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(settings.LLM_BASE_URL)
            services["llm_api"] = {
                "status": "reachable",
                "provider": "groq",
            }
    except Exception as e:
        logger.warning("LLM API health check failed: %s", e)
        services["llm_api"] = {
            "status": "unreachable",
            "provider": "groq",
            "detail": str(e),
        }

    # Check DOCX templates count
    try:
        templates_dir = settings.templates_absolute_path
        if templates_dir.exists():
            docx_files = list(templates_dir.glob("*.docx"))
            services["templates_docx"] = {
                "status": "ok",
                "count": len(docx_files),
            }
        else:
            services["templates_docx"] = {
                "status": "ok",
                "count": 0,
            }
    except Exception as e:
        logger.warning("Templates health check failed: %s", e)
        services["templates_docx"] = {
            "status": "error",
            "detail": str(e),
        }

    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "services": services,
    }
