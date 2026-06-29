"""DOCX Template Library API routes.

Provides endpoints for listing, viewing, uploading, and deleting
DOCX contract templates.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.api.dependencies import get_docx_template_service
from app.models.schemas import DocxTemplateHtmlResponse, DocxTemplateInfo
from app.services.docx_template_service import DocxTemplateService

router = APIRouter(prefix="/api/templates/docx", tags=["docx-templates"])


@router.get("", response_model=List[DocxTemplateInfo])
async def list_docx_templates(
    service: DocxTemplateService = Depends(get_docx_template_service),
) -> List[DocxTemplateInfo]:
    """List all available DOCX templates.

    Returns:
        List of template information objects.
    """
    templates = service.list_templates()
    return [DocxTemplateInfo(**t) for t in templates]


@router.get("/{template_id}/html", response_model=DocxTemplateHtmlResponse)
async def get_template_html(
    template_id: str,
    service: DocxTemplateService = Depends(get_docx_template_service),
) -> DocxTemplateHtmlResponse:
    """Get parsed HTML content of a DOCX template with variable highlighting.

    Args:
        template_id: URL-safe slug identifier of the template.

    Returns:
        Template HTML content with highlighted variables.

    Raises:
        HTTPException: 404 if template not found.
    """
    result = service.parse_to_html(template_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return DocxTemplateHtmlResponse(**result)


@router.post("/upload", response_model=DocxTemplateInfo)
async def upload_docx_template(
    file: UploadFile = File(...),
    service: DocxTemplateService = Depends(get_docx_template_service),
) -> DocxTemplateInfo:
    """Upload a new DOCX template.

    Accepts a .docx file and adds it to the template library.

    Args:
        file: Uploaded .docx file.

    Returns:
        Template information for the newly uploaded file.

    Raises:
        HTTPException: 400 if file is not a .docx file.
    """
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(
            status_code=400,
            detail="Only .docx files are accepted",
        )

    content = await file.read()
    try:
        result = service.save_uploaded_template(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return DocxTemplateInfo(**result)


@router.delete("/{template_id}", status_code=204)
async def delete_docx_template(
    template_id: str,
    service: DocxTemplateService = Depends(get_docx_template_service),
) -> None:
    """Delete a DOCX template.

    Args:
        template_id: URL-safe slug identifier of the template.

    Raises:
        HTTPException: 404 if template not found.
    """
    deleted = service.delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found")
