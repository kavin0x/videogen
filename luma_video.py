import os
from typing import Any, Dict, List, Literal, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

LUMA_API_BASE = "https://api.lumalabs.ai/dream-machine/v1"

VideoModel = Literal["ray-2", "ray-flash-2"]
AspectRatio = Literal["1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "9:21"]
OutputResolution = Literal["540p", "720p", "1080p", "4k"]
OutputDuration = Literal["5s", "9s"]


def generate_video_luma(
    prompt: str,
    *,
    model: VideoModel = "ray-2",
    aspect_ratio: AspectRatio = "16:9",
    loop: bool = False,
    keyframes: Optional[Dict[str, Any]] = None,
    resolution: Optional[OutputResolution] = None,
    duration: Optional[OutputDuration] = None,
    concepts: Optional[List[Dict[str, str]]] = None,
    callback_url: Optional[str] = None,
):
    """
    Create a Dream Machine **video** generation via the Luma API.

    See `Create a generation <https://docs.lumalabs.ai/reference/creategeneration>`_:
    ``POST /generations/video`` with JSON body including required ``model``.

    Args:
        prompt: Text prompt for the clip.
        model: ``ray-2`` (default) or ``ray-flash-2``.
        aspect_ratio: One of the documented aspect ratios.
        loop: Whether to loop the output.
        keyframes: Optional ``{\"frame0\": {...}, \"frame1\": {...}}`` for
            image / generation references.
        resolution: e.g. ``\"720p\"``, ``\"1080p\"``.
        duration: ``\"5s\"`` or ``\"9s\"`` where supported.
        concepts: Optional list of ``{\"key\": \"...\"}`` concept objects.
        callback_url: Optional webhook for state updates.

    Returns:
        Generation object JSON (``201`` response).
    """
    api_key = os.getenv("LUMA_API_KEY")
    if not api_key:
        raise ValueError("LUMA_API_KEY environment variable not set")

    url = f"{LUMA_API_BASE}/generations/video"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body: Dict[str, Any] = {
        "prompt": prompt,
        "model": model,
        "aspect_ratio": aspect_ratio,
        "loop": loop,
    }
    if keyframes is not None:
        body["keyframes"] = keyframes
    if resolution is not None:
        body["resolution"] = resolution
    if duration is not None:
        body["duration"] = duration
    if concepts is not None:
        body["concepts"] = concepts
    if callback_url is not None:
        body["callback_url"] = callback_url

    response = requests.post(url, headers=headers, json=body, timeout=120)
    if response.status_code >= 400:
        raise RuntimeError(f"Luma API error {response.status_code}: {response.text}")
    return response.json()


if __name__ == "__main__":
    video = generate_video_luma(
        "A futuristic cityscape with flying cars",
        model="ray-2",
        aspect_ratio="16:9",
        resolution="720p",
        duration="5s",
    )
    print(f"Video response: {video}")
