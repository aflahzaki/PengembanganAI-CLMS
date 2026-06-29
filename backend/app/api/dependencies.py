"""Shared dependency injection for API services.

Provides FastAPI dependency functions for injecting services
into route handlers.
"""

from functools import lru_cache

from app.rag.retriever import RetrieverService
from app.services.drafting_service import DraftingService
from app.services.docx_template_service import DocxTemplateService
from app.services.export_service import ExportService
from app.services.llm_service import LLMService


@lru_cache()
def get_retriever_service() -> RetrieverService:
    """Get or create the RetrieverService singleton.

    Returns:
        RetrieverService instance.
    """
    return RetrieverService()


@lru_cache()
def get_llm_service() -> LLMService:
    """Get or create the LLMService singleton.

    Returns:
        LLMService instance.
    """
    return LLMService()


def get_drafting_service() -> DraftingService:
    """Get a DraftingService instance with injected dependencies.

    Returns:
        DraftingService instance.
    """
    return DraftingService(
        retriever=get_retriever_service(),
        llm_service=get_llm_service(),
    )


def get_export_service() -> ExportService:
    """Get an ExportService instance.

    Returns:
        ExportService instance.
    """
    return ExportService()


@lru_cache()
def get_docx_template_service() -> DocxTemplateService:
    """Get or create the DocxTemplateService singleton.

    Returns:
        DocxTemplateService instance.
    """
    return DocxTemplateService()
