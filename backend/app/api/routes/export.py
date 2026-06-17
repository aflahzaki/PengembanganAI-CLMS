"""Export API routes for document conversion.

Provides endpoints for exporting contracts to various formats (DOCX).
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.api.dependencies import get_export_service
from app.models.schemas import ExportRequest
from app.services.export_service import ExportService

router = APIRouter(prefix="/api/export", tags=["export"])


@router.post("/docx")
async def export_to_docx(
    request: ExportRequest,
    export_service: ExportService = Depends(get_export_service),
) -> Response:
    """Export HTML contract content to DOCX format.

    Takes HTML content and converts it to a downloadable Word document.

    Args:
        request: ExportRequest with HTML content and options.
        export_service: Injected ExportService.

    Returns:
        DOCX file as a downloadable response.

    Raises:
        HTTPException: If export fails.
    """
    try:
        docx_bytes, filename = export_service.html_to_docx(
            html_content=request.html_content,
            filename=request.filename,
        )

        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(docx_bytes)),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export document: {str(e)}",
        )
