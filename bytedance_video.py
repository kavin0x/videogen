import os
import time
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# Data-plane base URLs (see BytePlus / Volcengine ModelArk "Base URL and authentication")
_DEFAULT_BYTEPLUS_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"
_DEFAULT_VOLCENGINE_BASE = "https://ark.cn-beijing.volces.com/api/v3"


def _ark_base_url() -> str:
    return (
        os.getenv("BYTEDANCE_ARK_BASE_URL")
        or os.getenv("ARK_API_BASE")
        or _DEFAULT_BYTEPLUS_BASE
    )


def _ark_api_key() -> str:
    key = os.getenv("ARK_API_KEY") or os.getenv("BYTEDANCE_API_KEY")
    if not key:
        raise ValueError(
            "Set ARK_API_KEY or BYTEDANCE_API_KEY (Bearer token for ModelArk / Ark)"
        )
    return key


def create_bytedance_video_task(
    prompt: str,
    *,
    model: Optional[str] = None,
    image_url: Optional[str] = None,
    extra_body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a **Seedance / Ark** video generation task (BytePlus or Volcengine).

    Uses the ModelArk data-plane endpoint
    ``POST {base}/contents/generations/tasks`` with Bearer auth, as documented
    for `Create a video generation task
    <https://docs.byteplus.com/en/docs/ModelArk/1520757>`_ /
    `Volcengine Ark video API
    <https://www.volcengine.com/docs/82379/1520757>`_.

    You must set ``BYTEDANCE_ARK_MODEL`` (or pass ``model``) to your **model id**
    or **endpoint id** from the Ark console.

    Args:
        prompt: Text prompt.
        model: Model or endpoint id (defaults to env ``BYTEDANCE_ARK_MODEL``).
        image_url: Optional reference image URL for image-to-video, if your
            account/model supports it (passed inside ``content``).
        extra_body: Optional additional JSON fields merged into the request body.

    Returns:
        Parsed JSON (includes task ``id`` for status polling when supported).
    """
    resolved_model = model or os.getenv("BYTEDANCE_ARK_MODEL")
    if not resolved_model:
        raise ValueError(
            "Pass model=... or set BYTEDANCE_ARK_MODEL to your Ark model / endpoint id"
        )

    base = _ark_base_url().rstrip("/")
    url = f"{base}/contents/generations/tasks"

    # Body shape varies slightly between Ark deployments; this matches common
    # ModelArk examples (top-level ``prompt`` plus optional ``image_url`` for i2v).
    body: Dict[str, Any] = {"model": resolved_model, "prompt": prompt}
    if image_url:
        body["image_url"] = image_url
    if extra_body:
        body.update(extra_body)

    headers = {
        "Authorization": f"Bearer {_ark_api_key()}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, json=body, timeout=120)
    if response.status_code >= 400:
        raise RuntimeError(
            f"Ark video task error {response.status_code}: {response.text}"
        )
    return response.json()


def get_bytedance_video_task(task_id: str) -> Dict[str, Any]:
    """GET task status: ``{base}/contents/generations/tasks/{task_id}``."""
    base = _ark_base_url().rstrip("/")
    url = f"{base}/contents/generations/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {_ark_api_key()}"}
    response = requests.get(url, headers=headers, timeout=60)
    if response.status_code >= 400:
        raise RuntimeError(
            f"Ark task retrieve error {response.status_code}: {response.text}"
        )
    return response.json()


def generate_video_bytedance(
    prompt: str,
    *,
    character_reference: Optional[str] = None,
    motion_style: Optional[str] = None,
    poll_interval_sec: float = 5.0,
    max_wait_sec: float = 600.0,
) -> Dict[str, Any]:
    """
    Submit a video task and poll until completion or timeout.

    ``motion_style`` is merged into ``extra_body`` as ``{\"motion_style\": ...}``
    if your endpoint accepts custom parameters (not all deployments do).

    ``character_reference`` is sent as an image URL content part when set.
    """
    extra: Dict[str, Any] = {}
    if motion_style:
        extra["motion_style"] = motion_style

    created = create_bytedance_video_task(
        prompt,
        image_url=character_reference,
        extra_body=extra or None,
    )
    task_id = created.get("id") or created.get("task_id")
    if not task_id:
        return created

    deadline = time.monotonic() + max_wait_sec
    last = created
    while time.monotonic() < deadline:
        status = (last.get("status") or last.get("state") or "").lower()
        if status in ("succeeded", "completed", "failed", "cancelled", "canceled"):
            return last
        time.sleep(poll_interval_sec)
        last = get_bytedance_video_task(str(task_id))
    return last


if __name__ == "__main__":
    print(
        "Configure BYTEDANCE_ARK_MODEL and ARK_API_KEY (or BYTEDANCE_API_KEY), then call "
        "create_bytedance_video_task or generate_video_bytedance."
    )
