from __future__ import annotations

import argparse
import json
import os
import shutil
import importlib
from pathlib import Path

from lib.env import load_env


def _require_env(name: str) -> str:
    v = (os.environ.get(name) or "").strip()
    if not v:
        raise SystemExit(
            f"Missing {name}. Set it in your environment (or .env) before running this script."
        )
    return v


def _readable_size(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024 or unit == "GB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n/1024:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}GB"


def _verify_image(path: Path) -> tuple[int, int, str]:
    try:
        Image = importlib.import_module("PIL.Image")  # type: ignore[assignment]
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "Pillow is required to verify image dimensions/format. Install `pillow` or skip verification."
        ) from e

    with Image.open(path) as im:  # type: ignore[attr-defined]
        w, h = im.size
        fmt = (im.format or "").lower()
        return w, h, fmt


def run_direct(*, prompt: str, out_path: Path) -> int:
    from integrations.openai_adapters import OpenAIImageGenerator

    _require_env("OPENAI_API_KEY")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    gen = OpenAIImageGenerator()
    data = gen.generate(prompt=prompt, fmt="webp", width=2000, height=1125)
    out_path.write_bytes(data)

    try:
        w, h, fmt = _verify_image(out_path)
    except Exception as e:
        print(f"⚠️ Generated file but could not verify dimensions: {e}")
        w = h = 0
        fmt = "(unknown)"
    print("✅ Direct image generation OK")
    print(f"- file: {out_path}")
    print(f"- size: {_readable_size(out_path.stat().st_size)}")
    print(f"- format: {fmt}")
    if w and h:
        print(f"- dimensions: {w}x{h}")
    return 0


def run_agent(
    *,
    slug: str,
    category: str | None,
    title: str,
    intro: str,
    picks: list[str],
    force: bool,
) -> int:
    from agents.image_generation_agent import ImageGenerationAgent
    from integrations.openai_adapters import OpenAIImageGenerator, OpenAIJsonLLM
    from schemas.hero_image import HeroImageRequest

    _require_env("OPENAI_API_KEY")

    public_images_dir = Path("site/public/images")
    post_dir = public_images_dir / "posts" / slug

    if force:
        shutil.rmtree(post_dir, ignore_errors=True)

    agent = ImageGenerationAgent(
        llm=OpenAIJsonLLM(),
        image_gen=OpenAIImageGenerator(),
        public_images_dir=str(public_images_dir),
        posts_subdir="posts",
    )

    req = HeroImageRequest(
        slug=slug,
        category=category,
        title=title,
        intro=intro,
        picks=picks,
        alternatives=None,
    )

    out = agent.run(req)

    # Verify output files exist on disk
    public_root = Path("site/public")
    disk_paths = {
        "hero": public_root / out.hero_image_path.lstrip("/"),
        "hero_home": public_root / (out.hero_image_home_path or "").lstrip("/") if out.hero_image_home_path else None,
        "hero_card": public_root / (out.hero_image_card_path or "").lstrip("/") if out.hero_image_card_path else None,
        "hero_source": public_root / (out.hero_source_path or "").lstrip("/") if out.hero_source_path else None,
    }

    print("✅ Agent hero generation returned:")
    print(json.dumps(out.model_dump(), indent=2))

    for k, p in disk_paths.items():
        if p is None:
            continue
        if not p.exists() or p.stat().st_size == 0:
            raise SystemExit(f"❌ Missing or empty output file: {k} -> {p}")
        try:
            w, h, fmt = _verify_image(p)
            dims = f" {w}x{h}" if w and h else ""
            print(f"- {k}: {p} ({_readable_size(p.stat().st_size)}) {fmt}{dims}")
        except Exception:
            print(f"- {k}: {p} ({_readable_size(p.stat().st_size)})")

    # Optional: compare against placeholder to detect backfill
    placeholder = public_images_dir / "placeholder-hero.webp"
    hero = disk_paths["hero"]
    if placeholder.exists() and hero and hero.exists():
        try:
            if placeholder.read_bytes() == hero.read_bytes():
                print("⚠️ hero.webp matches placeholder-hero.webp (likely placeholder backfill)")
        except Exception:
            pass

    return 0


def main() -> int:
    load_env()

    p = argparse.ArgumentParser(description="Test OpenAI image generation in isolation")
    p.add_argument("--mode", choices=["direct", "agent"], default="agent")
    p.add_argument("--slug", default="_image_test")
    p.add_argument("--category", default="travel")
    p.add_argument("--title", default="Travel rain gear essentials")
    p.add_argument(
        "--intro",
        default=(
            "A short, practical guide for UK travellers on what to pack for wet weather. "
            "Keep it UK-general and avoid city-specific framing."
        ),
    )
    p.add_argument(
        "--picks",
        default="Windproof umbrella; Lightweight poncho; Packable waterproof jacket",
        help="Semicolon-separated pick snippets",
    )
    p.add_argument(
        "--prompt",
        default=(
            "Minimal editorial illustration, clean shapes, generous white space. "
            "A cohesive scene representing travel rain gear essentials: an umbrella, a folded poncho, "
            "and a packable rain jacket near a small travel bag. No text, no logos."
        ),
    )
    p.add_argument("--out", default="output/debug_image.webp")
    p.add_argument("--force", action="store_true", help="Delete existing hero folder before generating")

    args = p.parse_args()

    if args.mode == "direct":
        return run_direct(prompt=str(args.prompt), out_path=Path(args.out))

    picks = [s.strip() for s in str(args.picks).split(";") if s.strip()]
    return run_agent(
        slug=str(args.slug),
        category=str(args.category) if args.category else None,
        title=str(args.title),
        intro=str(args.intro),
        picks=picks,
        force=bool(args.force),
    )


if __name__ == "__main__":
    raise SystemExit(main())
