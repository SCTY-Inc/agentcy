"""Direct Gemini SDK wrapper for structured output.

Thin wrapper around google-genai for:
- Structured output via Pydantic schemas
- Consistent error handling
- Tool execution support
"""

import json
import os
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

# Module-level client
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


def generate(
    prompt: str,
    model: str = "gemini-3-flash-preview",
    schema: type[T] | None = None,
    system: str | None = None,
    thinking: str = "low",
) -> T | str:
    """Generate content with optional structured output.

    Args:
        prompt: User prompt
        model: Model ID (default: gemini-3-flash-preview)
        schema: Pydantic model for structured output
        system: System instruction
        thinking: Thinking level (off, low, medium, high)

    Returns:
        Pydantic model instance if schema provided, else raw text
    """
    client = get_client()

    # Build config
    config_kwargs: dict = {}

    if thinking != "off":
        config_kwargs["thinking_config"] = types.ThinkingConfig(
            thinking_level=thinking
        )

    if system:
        config_kwargs["system_instruction"] = system

    if schema:
        config_kwargs["response_mime_type"] = "application/json"
        config_kwargs["response_schema"] = schema

    config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    if schema:
        # Parse JSON response into Pydantic model
        text = response.text
        data = json.loads(text)
        return schema(**data)

    return response.text


def generate_with_tools(
    prompt: str,
    tools: list,
    model: str = "gemini-3-flash-preview",
    system: str | None = None,
    max_iterations: int = 5,
) -> str:
    """Generate with tool calling support.

    Args:
        prompt: User prompt
        tools: List of callable functions
        model: Model ID
        system: System instruction
        max_iterations: Max tool call loops

    Returns:
        Final text response after tool execution
    """
    client = get_client()

    # Build tool declarations from functions
    tool_declarations = []
    tool_map = {}
    for tool in tools:
        tool_map[tool.__name__] = tool
        # google-genai can infer schema from function signature
        tool_declarations.append(tool)

    config_kwargs: dict = {
        "tools": tool_declarations,
        "thinking_config": types.ThinkingConfig(thinking_level="low"),
    }
    if system:
        config_kwargs["system_instruction"] = system

    config = types.GenerateContentConfig(**config_kwargs)

    # Initial request
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    # Handle tool calls iteratively
    messages = [{"role": "user", "parts": [{"text": prompt}]}]
    iterations = 0

    while iterations < max_iterations:
        # Check for tool calls in response
        if not response.candidates:
            break

        candidate = response.candidates[0]
        if not candidate.content.parts:
            break

        tool_calls = [
            p for p in candidate.content.parts
            if hasattr(p, "function_call") and p.function_call
        ]

        if not tool_calls:
            # No more tool calls - return final text
            return response.text

        # Execute tool calls
        messages.append({"role": "model", "parts": candidate.content.parts})

        tool_results = []
        for tc in tool_calls:
            fn_name = tc.function_call.name
            fn_args = dict(tc.function_call.args) if tc.function_call.args else {}

            if fn_name in tool_map:
                result = tool_map[fn_name](**fn_args)
                tool_results.append({
                    "function_response": {
                        "name": fn_name,
                        "response": {"result": result},
                    }
                })

        messages.append({"role": "user", "parts": tool_results})

        # Continue conversation
        response = client.models.generate_content(
            model=model,
            contents=messages,
            config=config,
        )
        iterations += 1

    return response.text if response.text else ""
