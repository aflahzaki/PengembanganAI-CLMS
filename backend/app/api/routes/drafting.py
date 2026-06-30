"""Drafting API routes for contract generation.

Provides endpoints for generating contract drafts from templates.
"""

import io
import json
import logging
from typing import Optional

from docx import Document

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.dependencies import get_drafting_service, get_llm_service
from app.models.schemas import AiGenerateResponse, DraftRequest, DraftResponse
from app.services.drafting_service import DraftingService
from app.services.llm_service import LLMService, PromptTooLargeError

logger = logging.getLogger(__name__)

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


@router.post("/draft/ai-generate", response_model=AiGenerateResponse)
async def ai_generate_contract(
    description: str = Form(..., description="Deskripsi kebutuhan kontrak"),
    variables: str = Form(..., description="JSON string of contract variables"),
    reference_file: Optional[UploadFile] = File(
        None, description="Optional reference DOCX file for structural guidance"
    ),
    llm_service: LLMService = Depends(get_llm_service),
) -> AiGenerateResponse:
    """Generate a contract draft using AI based on user description.

    Accepts a description of the desired contract, variable values as JSON,
    and an optional reference DOCX file. If a reference file is provided,
    its structure is extracted and used as a pattern for the generated contract.

    Args:
        description: Text description of the contract needed.
        variables: JSON string mapping variable names to values.
        reference_file: Optional .docx file to use as structural reference.
        llm_service: Injected LLMService.

    Returns:
        AiGenerateResponse with generated HTML content and metadata.

    Raises:
        HTTPException: If generation fails or input is invalid.
    """
    # Parse variables JSON
    try:
        variables_dict = json.loads(variables)
        if not isinstance(variables_dict, dict):
            raise ValueError("Variables must be a JSON object")
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid variables JSON: {str(e)}",
        )

    # Extract reference structure from DOCX if provided
    reference_structure: Optional[str] = None
    has_reference = False

    if reference_file is not None:
        if not reference_file.filename or not reference_file.filename.endswith(".docx"):
            raise HTTPException(
                status_code=400,
                detail="Reference file must be a .docx file",
            )

        try:
            content = await reference_file.read()

            # Enforce 10 MB file size limit
            max_file_size = 10 * 1024 * 1024  # 10 MB
            if len(content) > max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail="Reference file too large (max 10 MB)",
                )
            doc = Document(io.BytesIO(content))

            # Extract document structure: headings and paragraphs
            structure_parts = []
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if not text:
                    continue

                style_name = paragraph.style.name if paragraph.style else ""

                if "Heading" in style_name or style_name.startswith("Heading"):
                    level = style_name.replace("Heading", "").strip() or "1"
                    structure_parts.append(f"[Heading {level}] {text}")
                elif text.isupper() or (len(text) < 100 and text.endswith(":")):
                    # Likely a section title
                    structure_parts.append(f"[Section] {text}")
                else:
                    # Regular paragraph - include first 200 chars for context
                    truncated = text[:200] + "..." if len(text) > 200 else text
                    structure_parts.append(f"[Paragraph] {truncated}")

            reference_structure = "\n".join(structure_parts)
            has_reference = True
            logger.info(
                "Extracted reference structure from '%s': %d elements",
                reference_file.filename,
                len(structure_parts),
            )
        except Exception as e:
            logger.warning(
                "Failed to parse reference DOCX '%s': %s",
                reference_file.filename,
                str(e),
            )
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse reference DOCX file: {str(e)}",
            )

    # Generate contract using AI
    try:
        html_content = await llm_service.generate_ai_contract(
            description=description,
            variables=variables_dict,
            reference_structure=reference_structure,
        )

        metadata = {
            "model": llm_service.model_name,
            "has_reference": has_reference,
            "variables_count": len(variables_dict),
            "description_length": len(description),
        }

        return AiGenerateResponse(
            html_content=html_content,
            metadata=metadata,
        )
    except PromptTooLargeError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        logger.error("AI contract generation failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"AI contract generation failed: {str(e)}",
        )
