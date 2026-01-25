"""Gemini SDK wrapper for structured output.

Thin wrapper around google-genai providing:
- Structured output via Pydantic schemas
- Consistent error handling
- Tool execution support
"""

import json
import os

from google import genai
from google.genai import types
from pydantic import BaseModel

_client: genai.Client | None = None


def get_client() -> genai.Client:
    """Get or create Gemini client."""
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable required")
        _client = genai.Client(api_key=api_key)
    return _client


def generate[T: BaseModel](
    prompt: str,
    schema: type[T],
    system: str | None = None,
    model: str = "gemini-3-flash-preview",
    thinking: str = "low",
) -> T:
    """Generate structured output from prompt.

    Args:
        prompt: User prompt
        schema: Pydantic model for structured output
        system: Optional system instruction
        model: Model ID (default: gemini-3-flash-preview)
        thinking: Thinking level (off, low, medium, high)

    Returns:
        Pydantic model instance
    """
    client = get_client()

    config_kwargs: dict = {
        "response_mime_type": "application/json",
        "response_schema": schema,
    }

    if thinking != "off":
        config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=thinking)

    if system:
        config_kwargs["system_instruction"] = system

    config = types.GenerateContentConfig(**config_kwargs)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    data = json.loads(response.text)
    return schema(**data)
