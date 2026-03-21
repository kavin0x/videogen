import time
from typing import Literal, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

VideoSeconds = Literal["4", "8", 4, 8, 12, "12"]
VideoSize = Literal["720x1280", "1280x720", "1024x1792", "1792x1024"]


def generate_video_openai(
    prompt: str,
    *,
    seconds: Optional[VideoSeconds] = None,
    size: Optional[VideoSize] = None,
    input_reference: Optional[object] = None,
    wait: bool = False,
    poll_interval_sec: float = 2.0,
):
    """
    Start a Sora-class video job via the OpenAI Videos API.

    The server chooses the default video model unless you pass ``model`` through
    the SDK globally; this wrapper intentionally does not set ``model`` so your
    account default / API behavior stays unchanged.

    Args:
        prompt: Text description of the clip.
        seconds: Clip length (4, 8, or 12). Omit for API default.
        size: Resolution, e.g. ``\"1280x720\"``. Omit for API default.
        input_reference: Optional image reference per ``videos.create`` (file path,
            bytes, open file, or SDK-supported reference type).
        wait: If True, block until the job completes or fails (uses
            ``videos.create_and_poll``). If False, returns immediately with
            ``status`` typically ``queued`` / ``in_progress``.
        poll_interval_sec: Ignored unless you implement manual polling; reserved
            for future use.

    Returns:
        ``Video`` object from the OpenAI Python SDK.
    """
    _ = poll_interval_sec
    client = OpenAI()
    kwargs = {"prompt": prompt}
    if seconds is not None:
        kwargs["seconds"] = seconds
    if size is not None:
        kwargs["size"] = size
    if input_reference is not None:
        kwargs["input_reference"] = input_reference

    if wait:
        return client.videos.create_and_poll(**kwargs)

    video = client.videos.create(**kwargs)
    return video


def wait_for_openai_video(
    client: OpenAI, video_id: str, poll_interval_sec: float = 2.0
):
    """Poll ``videos.retrieve`` until the job finishes or fails."""
    while True:
        video = client.videos.retrieve(video_id)
        if video.status in ("completed", "failed"):
            return video
        time.sleep(poll_interval_sec)


if __name__ == "__main__":
    v = generate_video_openai("A calico cat playing a piano on stage", wait=False)
    print(f"Video ID: {v.id} status={v.status}")
