"""Tests for the image upload endpoint."""

import io
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture
def temp_uploads_dir():
    """Create a temporary directory to use as uploads dir during tests."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


def _create_minimal_png() -> bytes:
    """Create a minimal valid PNG file (1x1 pixel, red)."""
    # Minimal PNG: 8-byte signature + IHDR + IDAT + IEND
    import struct
    import zlib

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        raw = chunk_type + data
        return struct.pack(">I", len(data)) + raw + struct.pack(">I", zlib.crc32(raw) & 0xFFFFFFFF)

    signature = b"\x89PNG\r\n\x1a\n"
    # IHDR: width=1, height=1, bit_depth=8, color_type=2 (RGB)
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = _chunk(b"IHDR", ihdr_data)
    # IDAT: raw image data (filter byte 0 + RGB pixel FF0000)
    raw_data = b"\x00\xff\x00\x00"
    compressed = zlib.compress(raw_data)
    idat = _chunk(b"IDAT", compressed)
    # IEND
    iend = _chunk(b"IEND", b"")

    return signature + ihdr + idat + iend


class TestUploadImage:
    """Tests for POST /api/upload/image."""

    def test_upload_png_success(self, client, temp_uploads_dir):
        """Test successful PNG upload returns URL."""
        png_data = _create_minimal_png()

        with patch(
            "app.api.routes.upload._get_uploads_dir",
            return_value=temp_uploads_dir,
        ):
            response = client.post(
                "/api/upload/image",
                files={"file": ("test_signature.png", io.BytesIO(png_data), "image/png")},
            )

        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert data["url"].startswith("/uploads/")
        assert data["url"].endswith(".png")

        # Verify file exists on disk
        filename = data["url"].split("/")[-1]
        assert (temp_uploads_dir / filename).exists()

    def test_upload_jpg_success(self, client, temp_uploads_dir):
        """Test successful JPG upload returns URL."""
        # Minimal JPEG (not valid image but valid enough for extension test)
        jpg_data = b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9"

        with patch(
            "app.api.routes.upload._get_uploads_dir",
            return_value=temp_uploads_dir,
        ):
            response = client.post(
                "/api/upload/image",
                files={"file": ("photo.jpg", io.BytesIO(jpg_data), "image/jpeg")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["url"].startswith("/uploads/")
        assert data["url"].endswith(".jpg")

    def test_upload_jpeg_extension_success(self, client, temp_uploads_dir):
        """Test successful JPEG extension upload returns URL."""
        jpg_data = b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9"

        with patch(
            "app.api.routes.upload._get_uploads_dir",
            return_value=temp_uploads_dir,
        ):
            response = client.post(
                "/api/upload/image",
                files={"file": ("photo.jpeg", io.BytesIO(jpg_data), "image/jpeg")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["url"].endswith(".jpeg")

    def test_upload_invalid_extension_rejected(self, client):
        """Test that non-image files are rejected with 400."""
        response = client.post(
            "/api/upload/image",
            files={"file": ("malware.exe", io.BytesIO(b"bad content"), "application/octet-stream")},
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_upload_txt_rejected(self, client):
        """Test that .txt files are rejected with 400."""
        response = client.post(
            "/api/upload/image",
            files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_upload_no_file_returns_422(self, client):
        """Test that missing file field returns 422."""
        response = client.post("/api/upload/image")
        assert response.status_code == 422

    def test_upload_generates_unique_filenames(self, client, temp_uploads_dir):
        """Test that each upload generates a unique filename."""
        png_data = _create_minimal_png()

        urls = []
        with patch(
            "app.api.routes.upload._get_uploads_dir",
            return_value=temp_uploads_dir,
        ):
            for _ in range(3):
                response = client.post(
                    "/api/upload/image",
                    files={"file": ("same_name.png", io.BytesIO(png_data), "image/png")},
                )
                assert response.status_code == 200
                urls.append(response.json()["url"])

        # All URLs should be unique
        assert len(set(urls)) == 3
