
"""
Centralized configuration for Leaf Disease Detection System.

Loads application settings from the root .env file
and validates configuration before use.
"""

import os
import math
import logging

from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(
    dotenv_path=ENV_FILE,
    override=False
)


# --------------------------------------------------
# DEFAULT CONFIGURATION
# --------------------------------------------------

DEFAULT_MODEL_NAME = "qwen/qwen3.8-27b"

DEFAULT_TEMPERATURE = 0.3

DEFAULT_MAX_COMPLETION_TOKENS = 1024

DEFAULT_LOG_LEVEL = "INFO"

DEFAULT_LOG_FILE = "disease_detection.log"

SUPPORTED_IMAGE_FORMATS = (
    ".jpg",
    ".jpeg",
    ".png"
)


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

@dataclass
class AppConfig:
    """
    Centralized application configuration.
    """

    # API configuration
    groq_api_key: str

    model_name: str = DEFAULT_MODEL_NAME

    model_temperature: float = DEFAULT_TEMPERATURE

    max_completion_tokens: int = (
        DEFAULT_MAX_COMPLETION_TOKENS
    )

    # Logging configuration
    log_level: str = DEFAULT_LOG_LEVEL

    log_file: str = DEFAULT_LOG_FILE

    # Image configuration
    supported_formats: tuple = (
        SUPPORTED_IMAGE_FORMATS
    )

    # --------------------------------------------------
    # CONFIGURATION VALIDATION
    # --------------------------------------------------

    def __post_init__(self):
        """
        Validate configuration values.
        """

        if (
            not isinstance(self.groq_api_key, str)
            or not self.groq_api_key.strip()
        ):
            raise ValueError(
                "A valid GROQ_API_KEY is required."
            )

        if (
            not isinstance(self.model_name, str)
            or not self.model_name.strip()
        ):
            raise ValueError(
                "MODEL_NAME cannot be empty."
            )

        if (
            isinstance(self.model_temperature, bool)
            or not isinstance(
                self.model_temperature,
                (int, float)
            )
            or not math.isfinite(self.model_temperature)
        ):
            raise ValueError(
                "MODEL_TEMPERATURE must be a finite number."
            )

        if not 0 <= self.model_temperature <= 2:
            raise ValueError(
                "MODEL_TEMPERATURE must be between 0 and 2."
            )

        if (
            isinstance(self.max_completion_tokens, bool)
            or not isinstance(self.max_completion_tokens, int)
            or self.max_completion_tokens <= 0
        ):
            raise ValueError(
                "MAX_COMPLETION_TOKENS must be a positive integer."
            )

        self.log_level = self.log_level.upper()

        if self.log_level not in {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL"
        }:
            raise ValueError(
                f"Invalid logging level: {self.log_level}"
            )

        if not isinstance(self.log_file, str) or not self.log_file.strip():
            raise ValueError(
                "LOG_FILE cannot be empty."
            )

        normalized_formats = tuple(
            str(extension).lower()
            for extension in self.supported_formats
        )

        if not normalized_formats or any(
            extension not in SUPPORTED_IMAGE_FORMATS
            for extension in normalized_formats
        ):
            raise ValueError(
                "Only JPEG and PNG extensions are supported."
            )

        self.supported_formats = normalized_formats

    # --------------------------------------------------
    # LOAD CONFIGURATION FROM ENVIRONMENT
    # --------------------------------------------------

    @classmethod
    def from_env(cls) -> "AppConfig":
        """
        Load and validate configuration from environment variables.

        Required:
            GROQ_API_KEY

        Optional:
            MODEL_NAME
            MODEL_TEMPERATURE
            MAX_COMPLETION_TOKENS
            LOG_LEVEL
            LOG_FILE
        """

        # API key
        groq_api_key = os.getenv("GROQ_API_KEY")

        if not groq_api_key or not groq_api_key.strip():
            raise ValueError(
                "GROQ_API_KEY is missing. "
                "Add it to the project root .env file."
            )

        # Model temperature
        try:
            temperature = float(
                os.getenv(
                    "MODEL_TEMPERATURE",
                    str(DEFAULT_TEMPERATURE)
                )
            )
        except ValueError as error:
            raise ValueError(
                "MODEL_TEMPERATURE must be numeric."
            ) from error

        # Maximum completion tokens
        try:
            max_tokens = int(
                os.getenv(
                    "MAX_COMPLETION_TOKENS",
                    str(DEFAULT_MAX_COMPLETION_TOKENS)
                )
            )
        except ValueError as error:
            raise ValueError(
                "MAX_COMPLETION_TOKENS must be an integer."
            ) from error

        return cls(
            groq_api_key=groq_api_key,

            model_name=os.getenv(
                "MODEL_NAME",
                DEFAULT_MODEL_NAME
            ),

            model_temperature=temperature,

            max_completion_tokens=max_tokens,

            log_level=os.getenv(
                "LOG_LEVEL",
                DEFAULT_LOG_LEVEL
            ),

            log_file=os.getenv(
                "LOG_FILE",
                DEFAULT_LOG_FILE
            ),

            supported_formats=SUPPORTED_IMAGE_FORMATS
        )

    # --------------------------------------------------
    # LOGGING CONFIGURATION
    # --------------------------------------------------

    def configure_logging(self):
        """
        Configure application logging.

        Creates the log directory when a relative or
        absolute file path requires one.
        """

        log_path = Path(self.log_file)

        if not log_path.is_absolute():
            log_path = PROJECT_ROOT / log_path

        log_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        logging.basicConfig(
            level=getattr(logging, self.log_level),

            format=(
                "%(asctime)s - "
                "%(levelname)s - "
                "%(name)s - "
                "%(message)s"
            ),

            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(
                    log_path,
                    encoding="utf-8"
                )
            ],

            force=True
        )
