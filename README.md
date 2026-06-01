# Video Generation APIs

Thin Python wrappers around current **video generation** HTTP APIs and official SDKs. Model names and paths follow vendor docs as of early 2026 (verify in each provider’s console if a call fails).
> Note: the examples below import this repository's wrapper modules directly.

## Files

| Module | Provider | Notes |
|--------|----------|--------|
| `openai_video.py` | OpenAI | [Videos / Sora-class API](https://developers.openai.com/api/docs/guides/video-generation) — `videos.create` / `create_and_poll` (no `model` argument in wrapper; account default applies). |
| `runway_video.py` | Runway | [Developer API](https://docs.dev.runwayml.com/api/) — `text_to_video` / `image_to_video`, `X-Runway-Version: 2024-11-06`. |
| `google_veo_video.py` | Google | [Gemini Veo 3.1](https://ai.google.dev/gemini-api/docs/video) — `google-genai`, poll `operations.get`. |
| `luma_video.py` | Luma | [Dream Machine API](https://docs.lumalabs.ai/reference/creategeneration) — `POST .../generations/video`, requires `model` (`ray-2`, `ray-flash-2`). |
| `bytedance_video.py` | BytePlus / Volcengine | [ModelArk video tasks](https://docs.byteplus.com/en/docs/ModelArk/1520757) — `POST .../contents/generations/tasks`, Bearer `ARK_API_KEY`. |
| `meta_video.py` | Meta | **No public Movie Gen API** — raises `NotImplementedError`. |

## Setup

Use the project virtualenv (recommended):

```bash
cd /path/to/videogen
python3 -m venv .venv
source .venv/bin/activate
pip install openai python-dotenv requests google-genai
```

Install from PyPI:

```bash
pip install videogen
```

Copy `.env.example` to `.env` and fill in keys.

## Usage

### OpenAI

```python
from openai_video import generate_video_openai

job = generate_video_openai(
    "A calico cat playing a piano on stage",
    seconds="8",
    size="1280x720",
    wait=False,  # True → create_and_poll until completed/failed
)
print(job.id, job.status)
```

### Runway

```python
from runway_video import generate_video_runway

result = generate_video_runway(
    "A serene landscape with mountains and a river at sunset",
    turbo=True,   # gen4_turbo vs gen4.5
    ratio="1280:720",
    duration=5,
)
```

### Google Veo

```python
from google_veo_video import generate_video_veo

video = generate_video_veo(
    "A bustling city street during a rainy night",
    aspect_ratio="16:9",
    duration_seconds=8,
    resolution="1080p",  # optional: 720p, 1080p, 4k
    # reference_image_paths=["./ref1.png", "./ref2.png"],  # optional, local files
)
print(getattr(video, "uri", video))
```

### Luma

```python
from luma_video import generate_video_luma

video = generate_video_luma(
    "A futuristic cityscape with flying cars",
    model="ray-2",
    aspect_ratio="16:9",
    resolution="720p",
    duration="5s",
)
```

### BytePlus / Volcengine (Seedance)

Set `BYTEDANCE_ARK_MODEL` (or `model=` argument) to the **model id or endpoint id** from the Ark console.

```python
from bytedance_video import create_bytedance_video_task, generate_video_bytedance

task = create_bytedance_video_task("A cartoon character dancing in a park")
# or poll until a terminal status:
# result = generate_video_bytedance("...", character_reference="https://...")
```

### Meta

`generate_video_meta` is intentionally not implemented — there is no public Movie Gen REST API for arbitrary keys.

## PyPI Release Flow

This repository is configured to publish to PyPI from GitHub Releases via
trusted publishing.

1. Update version in [pyproject.toml](pyproject.toml) (for example `0.1.1`).
2. Create a GitHub Release with a tag that matches the version exactly.
    Tags like `v0.1.1` are also accepted.
3. The workflow in [.github/workflows/pypi-publish.yml](.github/workflows/pypi-publish.yml)
    builds and validates distributions, then publishes to PyPI.

### One-Time Setup

1. In PyPI, create project `videogen` (or publish once manually to create it).
2. In PyPI project settings, add a trusted publisher for this GitHub repo:
    `owner/repo`: this repository
    workflow: `pypi-publish.yml`
    environment: `pypi`
3. In GitHub repo settings, create environment `pypi` (optional protections
    recommended).
