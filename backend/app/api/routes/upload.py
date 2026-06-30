"""Upload API routes for image file handling.

Provides endpoints for uploading signature images and other image files
used in contract documents.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.config import settings

router = APIRouter(prefix="/api/upload", tags=["upload"])

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def _get_uploads_dir() -> Path:
    """Get the uploads directory path."""
    return settings.data_absolute_path / "uploads"


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file (PNG/JPG) for use in contract documents.

    Accepts a multipart form upload with a 'file' field containing
    an image. Returns the URL path to access the uploaded file.

    Args:
        file: The uploaded image file (must be png, jpg, or jpeg).

    Returns:
        JSON with 'url' field containing the path to the uploaded file.

    Raises:
        HTTPException: If the file is not a valid image type or exceeds size limit.
    """
    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed types: png, jpg, jpeg.",
        )

    # Validate content type
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="File must be an image (content-type must start with 'image/').",
        )

    # Read file content and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )

    # Validate magic bytes (PNG or JPEG)
    is_png = content[:8] == b"\x89PNG\r\n\x1a\n"
    is_jpeg = content[:3] == b"\xff\xd8\xff"
    if not (is_png or is_jpeg):
        raise HTTPException(
            status_code=400,
            detail="Invalid image content. File must be a valid PNG or JPEG image.",
        )

    # Generate unique filename
    unique_filename = f"{uuid.uuid4().hex}{ext}"

    # Save file
    uploads_dir = _get_uploads_dir()
    file_path = uploads_dir / unique_filename
    file_path.write_bytes(content)

    return {"url": f"/uploads/{unique_filename}"}
