"""Image generation tools using Replicate.

Tools are stubbed by default. Set AGENTCY_LIVE_TOOLS=1 to enable live API calls.
Requires REPLICATE_API_TOKEN for live generation.
"""

import os


def _is_live() -> bool:
    """Check if live tools are enabled."""
    return os.getenv("AGENTCY_LIVE_TOOLS", "").lower() in ("1", "true", "yes")


def generate_image(
    prompt: str,
    style: str = "photorealistic",
    aspect_ratio: str = "16:9",
) -> str:
    """Generate an image using AI.

    Args:
        prompt: Detailed description of the image to generate
        style: Visual style (photorealistic, illustration, minimalist, etc.)
        aspect_ratio: Image aspect ratio (16:9, 1:1, 9:16)

    Returns:
        URL of the generated image
    """
    if _is_live():
        return _live_generate(prompt, style, aspect_ratio)
    return _stub_generate(prompt, style, aspect_ratio)


def _stub_generate(prompt: str, style: str, aspect_ratio: str) -> str:
    """Return stub image URL for testing."""
    # Use a placeholder image service
    width, height = _aspect_to_dimensions(aspect_ratio)
    return f"https://placehold.co/{width}x{height}/png?text=Generated+Image"


def _live_generate(prompt: str, style: str, aspect_ratio: str) -> str:
    """Generate image using Replicate API."""
    import replicate

    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        raise ValueError("REPLICATE_API_TOKEN environment variable required")

    # Build enhanced prompt with style
    full_prompt = f"{prompt}. Style: {style}. High quality, professional."

    # Use FLUX for fast, high-quality generation
    output = replicate.run(
        "black-forest-labs/flux-schnell",
        input={
            "prompt": full_prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": "png",
            "output_quality": 90,
        },
    )

    # Replicate returns a list of URLs
    if isinstance(output, list) and len(output) > 0:
        return output[0]
    return str(output)


def _aspect_to_dimensions(aspect_ratio: str) -> tuple[int, int]:
    """Convert aspect ratio to pixel dimensions."""
    ratios = {
        "16:9": (1920, 1080),
        "9:16": (1080, 1920),
        "1:1": (1024, 1024),
        "4:3": (1024, 768),
        "3:4": (768, 1024),
    }
    return ratios.get(aspect_ratio, (1024, 1024))
