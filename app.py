
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from PIL import Image, ImageOps, UnidentifiedImageError
from io import BytesIO
from groq import RateLimitError
import logging

from utils import convert_image_to_base64_and_test


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Leaf Disease Detection API",
    description="AI-powered plant leaf disease detection API",
    version="1.1.0"
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_PIXELS = 25_000_000

ALLOWED_FORMATS = {"JPEG", "PNG"}


# --------------------------------------------------
# IMAGE VALIDATION AND NORMALIZATION
# --------------------------------------------------

def validate_and_normalize_image(contents: bytes) -> bytes:
    """
    Validate the uploaded image and normalize it to JPEG.

    This ensures that PNG and JPEG uploads are both
    compatible with the existing AI detection pipeline.
    """

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty."
        )

    try:
        with Image.open(BytesIO(contents)) as image:

            # Verify actual image format instead of
            # trusting the uploaded filename or MIME type.
            if image.format not in ALLOWED_FORMATS:
                raise HTTPException(
                    status_code=415,
                    detail="Unsupported image format. Upload JPG or PNG."
                )

            # Check image dimensions.
            width, height = image.size

            if width <= 0 or height <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image dimensions."
                )

            if width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=413,
                    detail="Image dimensions are too large."
                )

            # Verify image integrity.
            image.verify()

        # Reopen image after verify().
        with Image.open(BytesIO(contents)) as image:

            # Correct image orientation using EXIF metadata.
            image = ImageOps.exif_transpose(image)

            # Convert transparency to white background.
            if image.mode in ("RGBA", "LA") or "transparency" in image.info:
                rgba = image.convert("RGBA")
                background = Image.new(
                    "RGBA",
                    rgba.size,
                    (255, 255, 255, 255)
                )
                image = Image.alpha_composite(
                    background,
                    rgba
                ).convert("RGB")
            else:
                image = image.convert("RGB")

            # Normalize every accepted image to JPEG.
            output = BytesIO()

            image.save(
                output,
                format="JPEG",
                quality=95,
                optimize=True
            )

            return output.getvalue()

    except HTTPException:
        raise

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid image."
        )

    except Image.DecompressionBombError:
        raise HTTPException(
            status_code=413,
            detail="Image is too large to process safely."
        )

    except (OSError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Unable to read the uploaded image."
        )


# --------------------------------------------------
# DISEASE DETECTION ENDPOINT
# --------------------------------------------------

@app.post("/disease-detection-file")
async def disease_detection_file(
    file: UploadFile = File(...)
):
    """
    Detect plant diseases from an uploaded image.

    Accepts JPEG and PNG images through multipart/form-data.
    """

    try:
        logger.info("Received image upload: %s", file.filename)

        # Read at most MAX_FILE_SIZE + 1 bytes.
        # This prevents unlimited file reading.
        contents = await file.read(MAX_FILE_SIZE + 1)

        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Image exceeds the maximum allowed size of 10 MB."
            )

        # Validate and normalize the image.
        normalized_image = validate_and_normalize_image(
            contents
        )

        logger.info(
            "Image validated successfully. Processing with AI."
        )

        # Preserve the existing AI processing pipeline.
        result = convert_image_to_base64_and_test(
            normalized_image
        )

        if not isinstance(result, dict):
            logger.error("AI detector returned an invalid response.")

            raise HTTPException(
                status_code=502,
                detail="Disease analysis could not be completed."
            )

        logger.info("Disease detection completed successfully.")

        return JSONResponse(content=result)

    except HTTPException:
        raise

    except RateLimitError:
        logger.warning(
            "Groq API rate limit or token quota exceeded."
        )

        raise HTTPException(
            status_code=429,
            detail=(
                "AI analysis quota temporarily exhausted. "
                "Please try again after the quota resets."
            )
        )

    except Exception:
        logger.exception("Unexpected disease detection error.")

        raise HTTPException(
            status_code=500,
            detail="An internal error occurred during disease analysis."
        )

    finally:
        await file.close()


# --------------------------------------------------
# ROOT ENDPOINT
# --------------------------------------------------

@app.get("/")
async def root():
    """Return API information."""

    return {
        "message": "Leaf Disease Detection API",
        "version": "1.1.0",
        "status": "running",
        "endpoints": {
            "disease_detection_file": {
                "path": "/disease-detection-file",
                "method": "POST",
                "description": "Upload a JPEG or PNG image for disease detection"
            }
        }
    }
