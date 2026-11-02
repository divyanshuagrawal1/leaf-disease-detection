
"""
Leaf Disease Detection Engine
Groq API + Qwen Vision Model
"""

import os
import json
import base64
import binascii
import logging
import re

from typing import Dict, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv


# --------------------------------------------------
# LOGGING CONFIGURATION
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# ENVIRONMENT CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(
    dotenv_path=PROJECT_ROOT / ".env",
    override=False
)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "qwen/qwen3.8-27b"
)

DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 1024

API_TIMEOUT = 60.0
MAX_RETRIES = 2

ALLOWED_SEVERITIES = {
    "mild",
    "moderate",
    "severe",
    "none"
}


ALLOWED_DISEASE_TYPES = {
    "fungal",
    "bacterial",
    "viral",
    "pest",
    "nutrient deficiency",
    "healthy",
    "other",
    "invalid_image",
    "unknown"
}



# --------------------------------------------------
# DATA MODEL
# --------------------------------------------------

@dataclass
class DiseaseAnalysisResult:
    """
    Structured result of plant leaf disease analysis.
    """

    disease_detected: bool
    disease_name: Optional[str]
    disease_type: str
    severity: str
    confidence: float
    symptoms: List[str]
    possible_causes: List[str]
    treatment: List[str]

    analysis_timestamp: str = field(
        default_factory=lambda:
        datetime.now(timezone.utc).astimezone().isoformat()
    )


# --------------------------------------------------
# LEAF DISEASE DETECTOR
# --------------------------------------------------

class LeafDiseaseDetector:
    """
    AI-powered leaf disease detection using Groq and Qwen Vision.
    """

    MODEL_NAME = MODEL_NAME

    DEFAULT_TEMPERATURE = DEFAULT_TEMPERATURE
    DEFAULT_MAX_TOKENS = DEFAULT_MAX_TOKENS

    def __init__(self,api_key: Optional[str] = None):
        """
        Initialize the Groq API client.
        """

        self.api_key = (
            api_key or os.getenv("GROQ_API_KEY")
        )

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is missing. "
                "Configure it in your .env file."
            )

        self.client = Groq(
            api_key=self.api_key,
            timeout=API_TIMEOUT,
            max_retries=MAX_RETRIES
        )

        logger.info(
            "Leaf Disease Detector initialized using model: %s",
            self.MODEL_NAME
        )

    # --------------------------------------------------
    # ANALYSIS PROMPT
    # --------------------------------------------------

    
    def create_analysis_prompt(self) -> str:
        """
        Create instructions for reliable visual analysis.
        """

        return """
You are an agricultural plant health image analysis assistant.

Your task is to examine the uploaded image and determine
whether it contains a recognizable plant leaf suitable
for visual analysis.

IMPORTANT CLASSIFICATION RULES:

1. First determine whether the image contains a recognizable
   plant leaf.

2. If the image contains a person, animal, building, document,
   vehicle, unrelated object, or no recognizable plant leaf,
   classify it as invalid_image.

3. If it is a valid leaf, inspect visible symptoms such as:
   spots, lesions, discoloration, holes, mold, wilting,
   necrosis, drying, and abnormal leaf patterns.

4. NEVER classify a leaf as healthy simply because
   no recognizable disease has been identified.

5. A completely brown, dried, dead, decaying, severely
   wilted, or severely discolored leaf MUST NOT be
   classified as healthy.

6. Distinguish carefully between:
   - Healthy leaf
   - Diseased leaf
   - Dead, dried, or severely damaged leaf
   - Invalid or unidentifiable image
   - Uncertain classification

7. If a leaf is visibly dead, dried, or severely damaged
   but its specific cause cannot be determined:
   - Set disease_detected to true.
   - Set disease_name to
     "Dead or severely damaged leaf (cause undetermined)".
   - Set disease_type to "other".
   - Describe only the visible condition.
   - Do not invent a specific disease or cause.

8. If the leaf is visibly healthy, return
   disease_detected=false,
   disease_name=null,
   disease_type="healthy",
   and severity="none".

9. If a disease is suspected, identify the most likely
   disease only when there is sufficient visual evidence.

10. If the image is insufficient for reliable classification,
    do not assume that the leaf is healthy.
    Use disease_type="other" and explain the uncertainty
    in the symptoms.

11. Do not invent symptoms that are not visually supported.

12. Distinguish visual observations from possible causes.
    Do not claim laboratory confirmation.

13. Confidence must reflect the available visual evidence.
    It must not be artificially increased.

14. Confidence is an estimated visual assessment between
    0 and 100. It is NOT a statistically calibrated
    probability or independently measured diagnostic accuracy.

DISEASE CATEGORIES:

- fungal
- bacterial
- viral
- pest
- nutrient deficiency
- healthy
- other
- invalid_image

SEVERITY:

- mild
- moderate
- severe
- none

TREATMENT SAFETY:

- Provide general, practical crop-care guidance.
- Do not invent pesticide names, application dosages,
  or guaranteed cures.
- If chemical treatment may be needed, advise consulting
  a local agricultural expert and following the locally
  registered product label.
- Do not recommend disease treatment for a healthy leaf.
- For dead or severely dried leaves, provide general
  plant-care guidance without inventing the cause.
- For invalid images, ask the user to upload a clear leaf image.

OUTPUT REQUIREMENTS:

Return ONLY one valid JSON object.

Do not include Markdown code fences or explanatory text.

Use this exact structure:

{
    "disease_detected": true,
    "disease_name": "Disease name or condition",
    "disease_type": "fungal",
    "severity": "moderate",
    "confidence": 85,
    "symptoms": [
        "Visually observed symptom"
    ],
    "possible_causes": [
        "Possible cause"
    ],
    "treatment": [
        "Practical recommendation"
    ]
}

For a healthy leaf:

{
    "disease_detected": false,
    "disease_name": null,
    "disease_type": "healthy",
    "severity": "none",
    "confidence": 90,
    "symptoms": [
        "No obvious disease symptoms visible"
    ],
    "possible_causes": [],
    "treatment": [
        "Continue regular plant care"
    ]
}

For a dead, dried, or severely damaged leaf
with an undetermined cause:

{
    "disease_detected": true,
    "disease_name": "Dead or severely damaged leaf (cause undetermined)",
    "disease_type": "other",
    "severity": "severe",
    "confidence": 90,
    "symptoms": [
        "Leaf appears completely dried, brown, and severely damaged"
    ],
    "possible_causes": [
        "The specific cause cannot be determined from the image alone"
    ],
    "treatment": [
        "Inspect the plant and surrounding growing conditions",
        "Consult a local agricultural expert to determine the cause"
    ]
}

For an invalid image:

{
    "disease_detected": false,
    "disease_name": null,
    "disease_type": "invalid_image",
    "severity": "none",
    "confidence": 95,
    "symptoms": [
        "No recognizable plant leaf detected"
    ],
    "possible_causes": [],
    "treatment": [
        "Upload a clear image of a plant leaf"
    ]
}
        """


    # --------------------------------------------------
    # IMAGE VALIDATION
    # --------------------------------------------------

    @staticmethod
    def _validate_base64_image(
        base64_image: str
    ) -> tuple:
        """
        Validate Base64 encoding and actual image signature.

        Supports JPEG and PNG images.
        Returns normalized Base64 string and MIME type.
        """

        if not isinstance(base64_image, str):
            raise ValueError(
                "Image input must be a Base64 string."
            )

        base64_image = base64_image.strip()

        if not base64_image:
            raise ValueError(
                "Image data cannot be empty."
            )

        declared_mime = None

        # Handle data URL input.
        if base64_image.startswith("data:"):

            try:
                header, base64_image = base64_image.split(
                    ",", 1
                )

                declared_mime = header.split(";")[0][5:]

            except ValueError:
                raise ValueError(
                    "Invalid image data URL."
                )

        try:
            image_bytes = base64.b64decode(
                base64_image,
                validate=True
            )

        except (binascii.Error, ValueError):
            raise ValueError(
                "Invalid Base64 image encoding."
            )

        if not image_bytes:
            raise ValueError(
                "Decoded image is empty."
            )

        # Detect actual file format.
        if image_bytes.startswith(b"\xff\xd8\xff"):
            detected_mime = "image/jpeg"

        elif image_bytes.startswith(
            b"\x89PNG\r\n\x1a\n"
        ):
            detected_mime = "image/png"

        else:
            raise ValueError(
                "Unsupported image data. JPEG or PNG required."
            )

        # Ensure declared MIME matches actual image.
        if (
            declared_mime is not None
            and declared_mime != detected_mime
        ):
            raise ValueError(
                "Image MIME type does not match its content."
            )

        return base64_image, detected_mime

    # --------------------------------------------------
    # API REQUEST
    # --------------------------------------------------

    def analyze_leaf_image_base64(
        self,
        base64_image: str,
        temperature: float = None,
        max_tokens: int = None
    ) -> Dict:
        """
        Analyze a leaf image using the configured Groq vision model.
        """

        try:
            logger.info(
                "Starting leaf disease image analysis."
            )

            # Validate image input.
            validated_base64, mime_type = (
                self._validate_base64_image(base64_image)
            )

            # Preserve explicitly supplied zero values.
            if temperature is None:
                temperature = self.DEFAULT_TEMPERATURE

            if max_tokens is None:
                max_tokens = self.DEFAULT_MAX_TOKENS

            if not isinstance(temperature, (int, float)):
                raise ValueError(
                    "Temperature must be numeric."
                )

            if not 0 <= temperature <= 2:
                raise ValueError(
                    "Temperature must be between 0 and 2."
                )

            if (
                not isinstance(max_tokens, int)
                or isinstance(max_tokens, bool)
                or max_tokens <= 0
            ):
                raise ValueError(
                    "max_tokens must be a positive integer."
                )

            # Prepare image data URL.
            image_url = (
                f"data:{mime_type};base64,{validated_base64}"
            )

            logger.info(
                "Sending image to Groq model: %s",
                self.MODEL_NAME
            )

            # Groq API request.
            completion = self.client.chat.completions.create(

                model=self.MODEL_NAME,

                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.create_analysis_prompt()
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ],

                temperature=temperature,

                max_completion_tokens=max_tokens,

                top_p=1,

                stream=False
            )

            logger.info(
                "Groq API request completed successfully."
            )

            # Safely extract model response.
            if not completion.choices:
                raise ValueError(
                    "The AI model returned no response choices."
                )

            response_content = (
                completion.choices[0].message.content
            )

            if not response_content:
                raise ValueError(
                    "The AI model returned an empty response."
                )

            # Parse and validate JSON.
            result = self._parse_response(
                response_content
            )

            return asdict(result)

        except Exception:
            logger.exception(
                "Leaf disease analysis failed."
            )
            raise

    # --------------------------------------------------
    # JSON EXTRACTION
    # --------------------------------------------------

    @staticmethod
    def _extract_json(response_content: str) -> Dict:
        """
        Extract one JSON object from the AI response.
        """

        if not isinstance(response_content, str):
            raise ValueError(
                "AI response must be text."
            )

        cleaned = response_content.strip()

        # Remove Markdown fences if present.
        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned
        ).strip()

        # First attempt: complete response is JSON.
        try:
            data = json.loads(cleaned)

            if isinstance(data, dict):
                return data

        except json.JSONDecodeError:
            pass

        # Second attempt: locate JSON object in extra text.
        decoder = json.JSONDecoder()

        for index, character in enumerate(cleaned):

            if character != "{":
                continue

            try:
                data, _ = decoder.raw_decode(
                    cleaned[index:]
                )

                if isinstance(data, dict):
                    return data

            except json.JSONDecodeError:
                continue

        raise ValueError(
            "Unable to extract a valid JSON object "
            "from the AI response."
        )

    # --------------------------------------------------
    # RESPONSE VALIDATION
    # --------------------------------------------------

    @staticmethod
    def _validate_string_list(
        value,
        field_name: str
    ) -> List[str]:
        """
        Validate lists of textual observations.
        """

        if not isinstance(value, list):
            raise ValueError(
                f"{field_name} must be a list."
            )

        if len(value) > 20:
            raise ValueError(
                f"{field_name} contains too many entries."
            )

        if not all(
            isinstance(item, str) and item.strip()
            for item in value
        ):
            raise ValueError(
                f"{field_name} must contain non-empty strings."
            )

        return [
            item.strip()[:500]
            for item in value
        ]

    def _parse_response(
        self,
        response_content: str
    ) -> DiseaseAnalysisResult:
        """
        Parse and strictly validate the AI-generated response.
        """

        disease_data = self._extract_json(
            response_content
        )

        required_fields = {
            "disease_detected",
            "disease_name",
            "disease_type",
            "severity",
            "confidence",
            "symptoms",
            "possible_causes",
            "treatment"
        }

        missing_fields = (
            required_fields - disease_data.keys()
        )

        if missing_fields:
            raise ValueError(
                "AI response is missing required fields: "
                + ", ".join(sorted(missing_fields))
            )

        # Strict boolean validation.
        disease_detected = disease_data["disease_detected"]

        if not isinstance(disease_detected, bool):
            raise ValueError(
                "disease_detected must be a JSON boolean."
            )

        # Disease name validation.
        disease_name = disease_data["disease_name"]

        if disease_name is not None:

            if not isinstance(disease_name, str):
                raise ValueError(
                    "disease_name must be a string or null."
                )

            disease_name = disease_name.strip() or None

        # Disease type validation.
        disease_type = disease_data["disease_type"]

        if not isinstance(disease_type, str):
            raise ValueError(
                "disease_type must be a string."
            )

        disease_type = disease_type.strip().lower()

        if disease_type not in ALLOWED_DISEASE_TYPES:
            raise ValueError(
                f"Unsupported disease type: {disease_type}"
            )

        # Severity validation.
        severity = disease_data["severity"]

        if not isinstance(severity, str):
            raise ValueError(
                "severity must be a string."
            )

        severity = severity.strip().lower()

        if severity not in ALLOWED_SEVERITIES:
            raise ValueError(
                f"Unsupported severity: {severity}"
            )

        # Confidence validation.
        confidence = disease_data["confidence"]

        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
        ):
            raise ValueError(
                "Confidence must be numeric."
            )

        confidence = float(confidence)

        if not 0 <= confidence <= 100:
            raise ValueError(
                "Confidence must be between 0 and 100."
            )

        # Validate output lists.
        symptoms = self._validate_string_list(
            disease_data["symptoms"],
            "symptoms"
        )

        possible_causes = self._validate_string_list(
            disease_data["possible_causes"],
            "possible_causes"
        )

        treatment = self._validate_string_list(
            disease_data["treatment"],
            "treatment"
        )

        # Validate classification consistency.
        if disease_type == "invalid_image":

            if disease_detected or disease_name is not None:
                raise ValueError(
                    "Invalid images cannot have a detected disease."
                )

            if severity != "none":
                raise ValueError(
                    "Invalid images must have severity 'none'."
                )

        elif disease_type == "healthy":

            if disease_detected or disease_name is not None:
                raise ValueError(
                    "Healthy leaves cannot have a detected disease."
                )

            if severity != "none":
                raise ValueError(
                    "Healthy leaves must have severity 'none'."
                )

        elif disease_detected:

            if not disease_name:
                raise ValueError(
                    "Detected diseases must have a disease name."
                )

            if severity == "none":
                raise ValueError(
                    "Detected diseases must have a severity."
                )

        elif disease_name is not None:
            raise ValueError(
                "A negative disease result must have a null disease name."
            )

        logger.info(
            "AI response parsed and validated successfully."
        )

        return DiseaseAnalysisResult(
            disease_detected=disease_detected,
            disease_name=disease_name,
            disease_type=disease_type,
            severity=severity,
            confidence=confidence,
            symptoms=symptoms,
            possible_causes=possible_causes,
            treatment=treatment
        )


# --------------------------------------------------
# STANDALONE EXECUTION
# --------------------------------------------------

def main():
    """
    Initialize the detector for a basic configuration check.
    """

    try:
        detector = LeafDiseaseDetector()

        print(
            "Leaf Disease Detector initialized successfully!"
        )

        print(
            f"Active vision model: {detector.MODEL_NAME}"
        )

        print(
            "Ready to analyze JPEG and PNG leaf images."
        )

    except Exception:
        logger.exception(
            "Detector initialization failed."
        )

        raise


if __name__ == "__main__":
    main()
