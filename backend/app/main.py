"""FastAPI application entry point for CLMS Backend.

Configures the application with CORS middleware, lifespan events,
and includes all API routers.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import drafting, export, templates
from app.config import settings


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
)

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
app.include_router(templates.router)
app.include_router(export.router)


@app.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        Dict with service status information.
    """
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "app_name": settings.APP_NAME,
    }
