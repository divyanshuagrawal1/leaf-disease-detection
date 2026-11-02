
"""
Image processing utilities for Leaf Disease Detection.

Supports:
- JPEG and PNG image uploads
- Strict Base64 validation
- Actual image integrity verification
- Reusable AI detector initialization
- Structured disease analysis
"""

import base64
import binascii
import logging
import sys

from functools import lru_cache
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError


# --------------------------------------------------
# PATH CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

DETECTOR_DIR = PROJECT_ROOT / "Leaf Disease"
DETECTOR_FILE = DETECTOR_DIR / "main.py"

if not DETECTOR_FILE.is_file():
    raise FileNotFoundError(
        f"Detector file not found: {DETECTOR_FILE}"
    )

import importlib.util

SPEC = importlib.util.spec_from_file_location(
    "leaf_disease_detector_module",
    DETECTOR_FILE
)

if SPEC is None or SPEC.loader is None:
    raise ImportError(
        "Unable to load the leaf disease detector module."
    )

DETECTOR_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = DETECTOR_MODULE
SPEC.loader.exec_module(DETECTOR_MODULE)

LeafDiseaseDetector = DETECTOR_MODULE.LeafDiseaseDetector


# --------------------------------------------------
# LOGGING
# --------------------------------------------------

logger = logging.getLogger(__name__)


# --------------------------------------------------
# SUPPORTED IMAGE FORMATS
# --------------------------------------------------

SUPPORTED_FORMATS = {
    "JPEG": "image/jpeg",
    "PNG": "image/png"
}


# --------------------------------------------------
# IMAGE VALIDATION
# --------------------------------------------------

def validate_image_bytes(image_bytes: bytes) -> str:
    """
    Validate actual image content and integrity.

    Supports JPEG and PNG only.

    Returns:
        str: Detected image MIME type.
    """

    if not isinstance(image_bytes, bytes):
        raise TypeError("Image input must be bytes.")

    if not image_bytes:
        raise ValueError("Uploaded image is empty.")

    # Verify file signature before decoding.
    if image_bytes.startswith(b"\xff\xd8\xff"):
        expected_format = "JPEG"

    elif image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        expected_format = "PNG"

    else:
        raise ValueError(
            "Unsupported image format. "
            "Please upload a valid JPEG or PNG image."
        )

    try:
        # Verify the actual image structure.
        with Image.open(BytesIO(image_bytes)) as image:

            if image.format != expected_format:
                raise ValueError(
                    "Image signature does not match its format."
                )

            if image.width <= 0 or image.height <= 0:
                raise ValueError("Invalid image dimensions.")

            image.verify()

    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError
    ) as error:

        raise ValueError(
            "The uploaded image is corrupted or invalid."
        ) from error

    return SUPPORTED_FORMATS[expected_format]


# --------------------------------------------------
# DETECTOR INITIALIZATION
# --------------------------------------------------

@lru_cache(maxsize=1)
def get_detector():
    """
    Initialize and reuse a single detector instance.
    """

    logger.info("Initializing Leaf Disease Detector")

    detector = LeafDiseaseDetector()

    logger.info(
        "Detector class loaded from: %s",
        detector.__class__.__module__
    )

    logger.info(
        "Has analyze method: %s",
        hasattr(detector, "analyze_leaf_image_base64")
    )

    logger.info(
        "Detector methods: %s",
        [
            name for name in dir(detector)
            if "analyze" in name
        ]
    )

    return detector


# --------------------------------------------------
# BASE64 IMAGE ANALYSIS
# --------------------------------------------------

def test_with_base64_data(
    base64_image_string: str
) -> dict:
    """
    Analyze a Base64-encoded JPEG or PNG image.

    Args:
        base64_image_string:
            Base64 image data, with or without a data URL prefix.

    Returns:
        dict: Structured disease analysis result.
    """

    if not isinstance(base64_image_string, str):
        raise TypeError(
            "Image data must be a Base64 string."
        )

    base64_image_string = base64_image_string.strip()

    if not base64_image_string:
        raise ValueError(
            "Image data cannot be empty."
        )

    try:
        # Support data URLs.
        if base64_image_string.startswith("data:"):

            if "," not in base64_image_string:
                raise ValueError(
                    "Invalid image data URL."
                )

            header, base64_image_string = (
                base64_image_string.split(",", 1)
            )

            if ";base64" not in header.lower():
                raise ValueError(
                    "Image data URL must use Base64 encoding."
                )

        # Strict Base64 decoding.
        try:
            decoded_image = base64.b64decode(
                base64_image_string,
                validate=True
            )

        except (binascii.Error, ValueError) as error:
            raise ValueError(
                "Invalid Base64 image encoding."
            ) from error

        if not decoded_image:
            raise ValueError(
                "Decoded image is empty."
            )

        # Validate actual JPEG or PNG content.
        validate_image_bytes(decoded_image)

        logger.info(
            "Image format and integrity validated successfully."
        )

        # Get cached detector instance.
        detector = get_detector()

        # Perform AI analysis.
        result = detector.analyze_leaf_image_base64(
            base64_image_string
        )

        if not isinstance(result, dict):
            raise RuntimeError(
                "Detector returned an invalid response."
            )

        logger.info(
            "Disease analysis completed successfully."
        )

        return result

    except (ValueError, TypeError):
        logger.warning(
            "Invalid Base64 image input.",
            exc_info=True
        )
        raise

    except Exception:
        logger.exception(
            "Disease detection failed."
        )
        raise


# --------------------------------------------------
# IMAGE BYTES TO BASE64
# --------------------------------------------------

def convert_image_to_base64_and_test(
    image_bytes: bytes
) -> dict:
    """
    Validate image bytes, convert to Base64,
    and perform disease analysis.

    Supports JPEG and PNG images.

    Args:
        image_bytes:
            Raw image bytes.

    Returns:
        dict: Disease analysis result.
    """

    try:
        # Validate the uploaded image before encoding.
        mime_type = validate_image_bytes(
            image_bytes
        )

        logger.info(
            "Image validated successfully: %s",
            mime_type
        )

        # Convert image to Base64.
        base64_string = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        logger.info(
            "Image converted to Base64 successfully."
        )

        # Perform disease analysis.
        return test_with_base64_data(
            base64_string
        )

    except Exception:
        logger.exception(
            "Image conversion or analysis failed."
        )
        raise


# --------------------------------------------------
# STANDALONE EXECUTION
# --------------------------------------------------

def main():
    """
    Standalone utility test.
    """

    image_path = (
        PROJECT_ROOT
        / "Media"
        / "brown-spot-4 (1).jpg"
    )

    if not image_path.exists():
        raise FileNotFoundError(
            f"Sample image not found: {image_path}"
        )

    image_bytes = image_path.read_bytes()

    result = convert_image_to_base64_and_test(
        image_bytes
    )

    import json

    print(
        json.dumps(
            result,
            indent=4
        )
    )


if __name__ == "__main__":
    main()
