from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable

from openai import OpenAI

try:
    from PIL import Image, ImageOps  # type: ignore
except Exception:  # pragma: no cover
    Image = None  # type: ignore
    ImageOps = None  # type: ignore


@dataclass(frozen=True)
class HeroGenResult:
    hero_image_path: Path
    hero_image_home_path: Path
    hero_image_card_path: Path
    hero_source_path: Path


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _disk_path(public_dir: Path, url_path: str) -> Path:
    return public_dir / url_path.lstrip("/")


def _cover_resize(im: "Image.Image", width: int, height: int) -> "Image.Image":
    if ImageOps is None:
        return im
    return ImageOps.fit(im, (int(width), int(height)), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def _save_webp(im: "Image.Image", path: Path, *, quality: int = 85) -> None:
    _ensure_parent(path)
    im.save(str(path), format="WEBP", quality=int(quality), method=6)


def _build_prompt(*, title: str, category: str | None, picks: Iterable[str]) -> str:
    cat = (category or "").strip()
    picks_s = "; ".join([str(p).strip() for p in (picks or []) if str(p).strip()][:8])

    # Keep prompt simple + brand-safe (no logos, no text overlays).
    parts = [
        "Create a high-quality, photorealistic editorial hero image for a shopping guide article.",
        "No text, no logos, no watermarks.",
        "Clean composition, premium look, natural lighting, shallow depth of field.",
        f"Article title: {title}",
    ]
    if cat:
        parts.append(f"Category: {cat}")
    if picks_s:
        parts.append(f"Relevant items: {picks_s}")

    parts.append("UK audience. Modern lifestyle vibe.")
    return "\n".join(parts).strip()


def _generate_square_image_bytes(*, prompt: str, model: str | None = None) -> bytes:
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required to regenerate hero images")

    client = OpenAI(api_key=api_key)
    m = (model or os.environ.get("OPENAI_IMAGE_MODEL") or "gpt-image-1").strip()

    resp = client.images.generate(
        model=m,
        prompt=prompt,
        size="1024x1024",
    )

    first = resp.data[0]
    b64 = getattr(first, "b64_json", None) or getattr(first, "base64", None)
    if not b64:
        raise RuntimeError("Image API response did not include base64 data")

    return base64.b64decode(b64)


def generate_hero_image(
    *,
    public_dir: Path,
    slug: str,
    title: str,
    category: str | None = None,
    picks: list[str] | None = None,
    **_: Any,
) -> HeroGenResult:
    """Generate hero assets into `site/public/images/posts/<slug>/...`.

    This function is designed to be passed into `ensure_hero_assets_exist(... regen_fn=...)`.
    It writes the canonical files:
      - hero.webp (1600x900)
      - hero_home.webp (1200x630)
      - hero_card.webp (800x800)
      - hero_source.webp (1024x1024)
    """

    if Image is None or ImageOps is None:
        raise RuntimeError("Pillow is required for hero image generation")

    base_url = f"/images/posts/{slug}"
    hero_path = _disk_path(public_dir, f"{base_url}/hero.webp")
    home_path = _disk_path(public_dir, f"{base_url}/hero_home.webp")
    card_path = _disk_path(public_dir, f"{base_url}/hero_card.webp")
    source_path = _disk_path(public_dir, f"{base_url}/hero_source.webp")

    prompt = _build_prompt(title=title, category=category, picks=picks or [])
    raw = _generate_square_image_bytes(prompt=prompt)

    with Image.open(BytesIO(raw)) as im:
        im = im.convert("RGB")

        # Save source (square) and derived crops.
        _save_webp(im, source_path, quality=90)

        hero = _cover_resize(im, 1600, 900)
        _save_webp(hero, hero_path, quality=85)

        home = _cover_resize(im, 1200, 630)
        _save_webp(home, home_path, quality=85)

        card = _cover_resize(im, 800, 800)
        _save_webp(card, card_path, quality=85)

    return HeroGenResult(
        hero_image_path=hero_path,
        hero_image_home_path=home_path,
        hero_image_card_path=card_path,
        hero_source_path=source_path,
    )
