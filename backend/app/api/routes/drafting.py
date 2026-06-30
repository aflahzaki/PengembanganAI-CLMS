"""Drafting API routes for contract generation.

Provides endpoints for generating contract drafts from templates,
including AI-powered generation with rate limiting.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.dependencies import get_drafting_service, get_llm_service
from app.models.schemas import AiGenerateRequest, DraftRequest, DraftResponse
from app.services.drafting_service import DraftingService
from app.services.llm_service import LLMService

router = APIRouter(prefix="/api", tags=["drafting"])

limiter = Limiter(key_func=get_remote_address)


@router.post("/draft", response_model=DraftResponse)
@limiter.limit("60/minute")
async def create_draft(
    request: Request,
    body: DraftRequest,
    drafting_service: DraftingService = Depends(get_drafting_service),
) -> DraftResponse:
    """Generate a contract draft from a template.

    Takes a template name, variable values, and options to produce
    a complete contract draft in HTML format.

    Rate limited to 60 requests per minute per IP.

    Args:
        request: FastAPI Request object (for rate limiting).
        body: DraftRequest with template name and variables.
        drafting_service: Injected DraftingService.

    Returns:
        DraftResponse with generated HTML and metadata.

    Raises:
        HTTPException: If draft generation fails.
    """
    try:
        response = await drafting_service.generate_draft(body)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate draft: {str(e)}",
        )


@router.post("/draft/ai-generate", response_model=DraftResponse)
@limiter.limit("60/minute")
async def ai_generate_draft(
    request: Request,
    body: AiGenerateRequest,
    drafting_service: DraftingService = Depends(get_drafting_service),
    llm_service: LLMService = Depends(get_llm_service),
) -> DraftResponse:
    """Generate a contract draft using AI based on a description.

    Uses the LLM to generate a contract draft based on the provided
    description and optional variables. Rate limited to 60 requests
    per minute per IP.

    Args:
        request: FastAPI Request object (for rate limiting).
        body: AiGenerateRequest with description, template name, and variables.
        drafting_service: Injected DraftingService.
        llm_service: Injected LLMService.

    Returns:
        DraftResponse with AI-generated HTML and metadata.

    Raises:
        HTTPException: If description exceeds 2000 characters or generation fails.
    """
    # Additional validation for description length
    if len(body.description) > 2000:
        raise HTTPException(
            status_code=422,
            detail="description must be at most 2000 characters",
        )

    try:
        # Build a draft request from the AI generate request
        draft_request = DraftRequest(
            template_name=body.template_name,
            variables=body.variables,
            include_optional=True,
        )
        response = await drafting_service.generate_draft(draft_request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate AI draft: {str(e)}",
        )
