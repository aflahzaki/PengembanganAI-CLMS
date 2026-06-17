"""Drafting API routes for contract generation.

Provides endpoints for generating contract drafts from templates.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_drafting_service
from app.models.schemas import DraftRequest, DraftResponse
from app.services.drafting_service import DraftingService

router = APIRouter(prefix="/api", tags=["drafting"])


@router.post("/draft", response_model=DraftResponse)
async def create_draft(
    request: DraftRequest,
    drafting_service: DraftingService = Depends(get_drafting_service),
) -> DraftResponse:
    """Generate a contract draft from a template.

    Takes a template name, variable values, and options to produce
    a complete contract draft in HTML format.

    Args:
        request: DraftRequest with template name and variables.
        drafting_service: Injected DraftingService.

    Returns:
        DraftResponse with generated HTML and metadata.

    Raises:
        HTTPException: If draft generation fails.
    """
    try:
        response = await drafting_service.generate_draft(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate draft: {str(e)}",
        )
