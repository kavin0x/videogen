import os
import time
from pathlib import Path
from typing import List, Literal, Optional, Sequence, Union

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

AspectRatio = Literal["16:9", "9:16"]
Resolution = Literal["720p", "1080p", "4k"]

MODEL_VEO_3_1 = "veo-3.1-generate-preview"


def _video_response_videos(operation: types.GenerateVideosOperation):
    """Normalize access to generated videos after polling."""
    payload = operation.result or operation.response
    if not payload or not payload.generated_videos:
        raise RuntimeError(
            "Video generation finished but no generated_videos in response"
        )
    return payload.generated_videos


def generate_video_veo(
    prompt: str,
    *,
    reference_image_paths: Optional[Sequence[Union[str, Path]]] = None,
    aspect_ratio: AspectRatio = "16:9",
    duration_seconds: Optional[int] = 8,
    resolution: Optional[Resolution] = None,
    poll_interval_sec: float = 10.0,
    download_path: Optional[Union[str, Path]] = None,
    model: str = MODEL_VEO_3_1,
):
    """
    Generate video with Google Veo via the Gemini API (``google-genai``).

    Follows the flow in the
    `Gemini video generation docs <https://ai.google.dev/gemini-api/docs/video>`_:
    long-running operation, poll with ``client.operations.get``, then optional
    download.

    Reference images must be **local files** (SDK ``Image`` uses bytes or GCS URI;
    there is no generic HTTP URL field). Up to three images are supported as
    ``VideoGenerationReferenceImage`` with ``reference_type`` ``ASSET``.

    Args:
        prompt: Text description of the video.
        reference_image_paths: Optional paths to reference images on disk.
        aspect_ratio: ``\"16:9\"`` (landscape) or ``\"9:16\"`` (portrait).
        duration_seconds: Target duration; omit to let the API use its default.
        resolution: Optional ``\"720p\"``, ``\"1080p\"``, or ``\"4k\"``.
        poll_interval_sec: Sleep between ``operations.get`` polls.
        download_path: If set, download the first output video to this path.
        model: Veo model id (default ``veo-3.1-generate-preview``).

    Returns:
        The first ``Video`` object from the completed operation.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")

    client = genai.Client(api_key=api_key)

    ref_images: Optional[List[types.VideoGenerationReferenceImage]] = None
    if reference_image_paths:
        ref_images = []
        for p in reference_image_paths[:3]:
            path = Path(p).expanduser()
            img = types.Image.from_file(location=str(path))
            ref_images.append(
                types.VideoGenerationReferenceImage(
                    image=img,
                    reference_type=types.VideoGenerationReferenceType.ASSET,
                )
            )

    config_kwargs = {"aspect_ratio": aspect_ratio}
    if duration_seconds is not None:
        config_kwargs["duration_seconds"] = duration_seconds
    if resolution is not None:
        config_kwargs["resolution"] = resolution
    if ref_images is not None:
        config_kwargs["reference_images"] = ref_images

    config = types.GenerateVideosConfig(**config_kwargs)

    operation = client.models.generate_videos(
        model=model,
        source=types.GenerateVideosSource(prompt=prompt),
        config=config,
    )

    while not operation.done:
        time.sleep(poll_interval_sec)
        operation = client.operations.get(operation)

    if operation.error:
        raise RuntimeError(f"Veo generation failed: {operation.error}")

    generated = _video_response_videos(operation)[0].video
    if download_path and generated:
        client.files.download(file=generated)
        generated.save(str(download_path))
    return generated


if __name__ == "__main__":
    video = generate_video_veo(
        "A bustling city street during a rainy night",
        aspect_ratio="16:9",
        duration_seconds=8,
    )
    uri = getattr(video, "uri", None) or video
    print(f"Generated video: {uri}")
