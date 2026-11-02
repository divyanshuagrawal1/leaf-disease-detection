
"""
Pytest API Test Suite for Leaf Disease Detection.

Tests:
1. Root endpoint
2. Valid JPEG upload
3. Valid PNG upload
4. Empty image rejection
5. Fake image rejection
6. PDF rejection
7. BMP rejection
8. Oversized image rejection
"""

from io import BytesIO
from pathlib import Path

import pytest
import requests
from PIL import Image


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

API_URL = "http://127.0.0.1:8000"
DETECTION_ENDPOINT = f"{API_URL}/disease-detection-file"

PROJECT_DIR = Path(__file__).resolve().parent
MEDIA_DIR = PROJECT_DIR / "Media"

TIMEOUT = (5, 120)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


# --------------------------------------------------
# ROOT ENDPOINT
# --------------------------------------------------

def test_root_endpoint():
    """Verify that the API root endpoint is working."""

    response = requests.get(
        API_URL,
        timeout=TIMEOUT
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, dict)
    assert data.get("status") == "running"
    assert "disease_detection_file" in data.get("endpoints", {})


# --------------------------------------------------
# VALID IMAGE UPLOADS
# --------------------------------------------------

@pytest.mark.parametrize(
    "image_name",
    [
        "brown-spot-4 (1).jpg",
        "test-leaf.png"
    ]
)
def test_image_upload(image_name):
    """Test valid JPEG and PNG image uploads."""

    image_path = MEDIA_DIR / image_name

    assert image_path.is_file(), (
        f"Test image not found: {image_path}"
    )

    with image_path.open("rb") as image_file:

        files = {
            "file": (
                image_path.name,
                image_file,
                "application/octet-stream"
            )
        }

        response = requests.post(
            DETECTION_ENDPOINT,
            files=files,
            timeout=TIMEOUT
        )

    assert response.status_code == 200

    result = response.json()

    assert isinstance(result, dict)
    assert "disease_detected" in result
    assert "disease_type" in result
    assert "severity" in result
    assert "confidence" in result


# --------------------------------------------------
# INVALID IMAGE UPLOADS
# --------------------------------------------------

@pytest.mark.parametrize(
    "filename,contents,expected_status",
    [
        ("empty.jpg", b"", 400),

        (
            "fake-image.jpg",
            b"This is not a real image.",
            400
        ),

        (
            "document.pdf",
            b"%PDF-1.4 fake PDF content",
            400
        )
    ]
)
def test_invalid_upload(
    filename,
    contents,
    expected_status
):
    """Verify rejection of invalid image uploads."""

    files = {
        "file": (
            filename,
            contents,
            "application/octet-stream"
        )
    }

    response = requests.post(
        DETECTION_ENDPOINT,
        files=files,
        timeout=TIMEOUT
    )

    assert response.status_code == expected_status


# --------------------------------------------------
# UNSUPPORTED IMAGE FORMAT
# --------------------------------------------------

def test_bmp_upload_rejected():
    """Verify that valid BMP images are rejected."""

    source = MEDIA_DIR / "brown-spot-4 (1).jpg"

    assert source.is_file(), (
        f"Source image not found: {source}"
    )

    with Image.open(source) as image:
        output = BytesIO()
        image.save(output, format="BMP")
        bmp_contents = output.getvalue()

    files = {
        "file": (
            "unsupported.bmp",
            bmp_contents,
            "application/octet-stream"
        )
    }

    response = requests.post(
        DETECTION_ENDPOINT,
        files=files,
        timeout=TIMEOUT
    )

    assert response.status_code == 415


# --------------------------------------------------
# FILE SIZE VALIDATION
# --------------------------------------------------

def test_oversized_upload_rejected():
    """Verify that uploads exceeding 10 MB are rejected."""

    oversized_contents = (
        b"x" * (MAX_UPLOAD_SIZE + 1)
    )

    files = {
        "file": (
            "oversized.jpg",
            oversized_contents,
            "application/octet-stream"
        )
    }

    response = requests.post(
        DETECTION_ENDPOINT,
        files=files,
        timeout=TIMEOUT
    )

    assert response.status_code == 413
