import os
from typing import Literal, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

RUNWAY_API_BASE = "https://api.dev.runwayml.com"
RUNWAY_API_VERSION = "2024-11-06"

RunwayModel = Literal["gen4.5", "gen4_turbo", "gen3a_turbo"]
RunwayRatio = Literal[
    "1280:720",
    "720:1280",
    "960:960",
    "1104:832",
    "832:1104",
    "1584:672",
]


def _runway_api_key() -> str:
    key = os.getenv("RUNWAYML_API_SECRET") or os.getenv("RUNWAY_API_KEY")
    if not key:
        raise ValueError(
            "Set RUNWAYML_API_SECRET (preferred) or RUNWAY_API_KEY for Runway API access"
        )
    return key


def generate_video_runway(
    prompt: str,
    *,
    turbo: bool = True,
    reference_image: Optional[str] = None,
    ratio: RunwayRatio = "1280:720",
    duration: int = 5,
    model: Optional[RunwayModel] = None,
):
    """
    Generate video using the Runway developer API (Gen-4 family).

    Uses ``POST /v1/text_to_video`` or ``POST /v1/image_to_video`` per the
    `Runway API reference <https://docs.dev.runwayml.com/api/>`_.

    Args:
        prompt: Text prompt (``promptText`` in the API).
        turbo: If True (default), uses ``gen4_turbo``; otherwise ``gen4.5``.
        reference_image: Optional image URL or data URI for image-to-video.
        ratio: Aspect / resolution preset, e.g. ``\"1280:720\"``.
        duration: Clip length in seconds (commonly 5, 8, or 10 depending on model).
        model: Override model id (e.g. ``\"gen4.5\"``, ``\"gen4_turbo\"``).

    Returns:
        Parsed JSON dict from the API.
    """
    api_key = _runway_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Runway-Version": RUNWAY_API_VERSION,
    }

    resolved_model: RunwayModel = model or ("gen4_turbo" if turbo else "gen4.5")

    if reference_image:
        url = f"{RUNWAY_API_BASE}/v1/image_to_video"
        body = {
            "model": resolved_model,
            "promptText": prompt,
            "promptImage": reference_image,
            "ratio": ratio,
            "duration": duration,
        }
    else:
        url = f"{RUNWAY_API_BASE}/v1/text_to_video"
        body = {
            "model": resolved_model,
            "promptText": prompt,
            "ratio": ratio,
            "duration": duration,
        }

    response = requests.post(url, headers=headers, json=body, timeout=120)
    if response.status_code >= 400:
        raise RuntimeError(f"Runway API error {response.status_code}: {response.text}")
    return response.json()


if __name__ == "__main__":
    out = generate_video_runway(
        "A serene landscape with mountains and a river at sunset",
        turbo=True,
    )
    print(f"Runway response: {out}")
