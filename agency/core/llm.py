"""Gemini SDK wrapper for structured output.

Thin wrapper around google-genai providing:
- Structured output via Pydantic schemas
- Consistent error handling
- Configurable model via AGENCY_MODEL env var
"""

import json
import os

from google import genai
from google.genai import types
from pydantic import BaseModel

_client: genai.Client | None = None

DEFAULT_MODEL = "gemini-2.0-flash"


def get_model() -> str:
    """Get model from env or default."""
    return os.getenv("AGENCY_MODEL", DEFAULT_MODEL)


def get_client() -> genai.Client:
    """Get or create Gemini client."""
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable required")
        _client = genai.Client(api_key=api_key)
    return _client


class LLMError(Exception):
    """Error during LLM generation."""

    pass


def generate[T: BaseModel](
    prompt: str,
    schema: type[T],
    system: str | None = None,
    model: str | None = None,
    thinking: str = "low",
    retries: int = 2,
) -> T:
    """Generate structured output from prompt.

    Args:
        prompt: User prompt
        schema: Pydantic model for structured output
        system: Optional system instruction
        model: Model ID (default: AGENCY_MODEL env or gemini-2.0-flash)
        thinking: Thinking level (off, low, medium, high)
        retries: Number of retries on failure

    Returns:
        Pydantic model instance

    Raises:
        LLMError: If generation fails after retries
    """
    client = get_client()
    model = model or get_model()

    config_kwargs: dict = {
        "response_mime_type": "application/json",
        "response_schema": schema,
    }

    if thinking != "off":
        config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=thinking)

    if system:
        config_kwargs["system_instruction"] = system

    config = types.GenerateContentConfig(**config_kwargs)

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )

            if not response.text:
                raise LLMError("Empty response from model")

            data = json.loads(response.text)
            return schema(**data)

        except json.JSONDecodeError as e:
            last_error = LLMError(f"Invalid JSON from model: {e}")
        except Exception as e:
            last_error = LLMError(f"Generation failed: {e}")

        if attempt < retries:
            continue

    raise last_error or LLMError("Generation failed")
