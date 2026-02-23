from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from lib.validation.markdown_frontmatter import parse_markdown_frontmatter, rebuild_markdown_with_frontmatter
from lib.pick_image_enrichment import enrich_pick_images_for_markdown
from pipeline.hero_self_heal import ensure_hero_assets_exist


@dataclass(frozen=True)
class HydrationResult:
    post_slug: str
    post_path: Path
    package_dir: Path
    hero_paths: dict[str, str]
    pick_images_updated: int
    pick_images_skipped: int
    pick_image_errors: list[str]


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return data


def _extract_frontmatter(md: str) -> dict[str, Any]:
    text = (md or "").replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    fm_text = text[4:end]
    fm = yaml.safe_load(fm_text) or {}
    return fm if isinstance(fm, dict) else {}


def _inject_missing_frontmatter_scalars(md: str, updates: dict[str, str]) -> str:
    """Inject missing scalar keys after the first '---\n'.

    Keeps formatting stable and avoids re-dumping YAML.
    """

    text = (md or "").replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("---\n"):
        # Create frontmatter if absent.
        lines = ["---"]
        for k, v in updates.items():
            lines.append(f'{k}: "{v}"')
        lines.append("---")
        return "\n".join(lines) + "\n\n" + text.lstrip("\n")

    fm = _extract_frontmatter(text)
    missing_lines: list[str] = []
    for k, v in updates.items():
        if k not in fm:
            missing_lines.append(f'{k}: "{v}"')

    if not missing_lines:
        return text

    insert_at = 4  # len('---\n')
    return text[:insert_at] + "\n".join(missing_lines) + "\n" + text[insert_at:]


def _preserve_existing_product_images(*, existing_md: str, new_md: str) -> str:
    """When overwriting a post, preserve products[].image values if present.

    This prevents re-running hydration from wiping managed-site enrichments.
    """

    existing = parse_markdown_frontmatter(existing_md)
    incoming = parse_markdown_frontmatter(new_md)

    existing_products = existing.data.get("products")
    incoming_products = incoming.data.get("products")

    if not isinstance(existing_products, list) or not isinstance(incoming_products, list):
        return new_md

    image_by_pick_id: dict[str, str] = {}
    for p in existing_products:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("pick_id") or "").strip()
        img = p.get("image")
        if pid and isinstance(img, str) and img.strip():
            image_by_pick_id[pid] = img.strip()

    if not image_by_pick_id:
        return new_md

    changed = False
    for p in incoming_products:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("pick_id") or "").strip()
        if not pid:
            continue

        img = p.get("image")
        if isinstance(img, str) and img.strip():
            continue

        preserved = image_by_pick_id.get(pid)
        if preserved:
            p["image"] = preserved
            changed = True

    if not changed:
        return new_md

    incoming.data["products"] = incoming_products
    return rebuild_markdown_with_frontmatter(incoming.data, incoming.body)


def hydrate_blog_post_from_package(
    *,
    repo_root: Path,
    package_dir: Path,
    overwrite: bool = False,
    enrich_pick_images: bool = True,
    dry_run: bool = False,
    regen_hero_if_possible: bool = True,
) -> HydrationResult:
    """Apply a Content Package v1 into the managed site's Astro structure.

    Writes the post into `site/src/content/posts/YYYY-MM-DD-{slug}.md`.

    Then (optionally):
      - enrich pick images (downloads into site/public/images/picks/<post_slug>/...)
      - ensure hero assets exist (regenerates if OPENAI_API_KEY is set; otherwise uses placeholder)

    `dry_run` skips networked pick-image downloads and hero regen, but will still write files.
    """

    manifest_path = package_dir / "manifest.json"
    post_src_path = package_dir / "post.md"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest.json in {package_dir}")
    if not post_src_path.exists():
        raise FileNotFoundError(f"Missing post.md in {package_dir}")

    manifest = _read_json(manifest_path)
    if str(manifest.get("version")) != "1":
        raise ValueError(f"Unsupported package version: {manifest.get('version')}")

    publish_date = date.fromisoformat(str(manifest.get("publish_date")))
    slug = str(manifest.get("slug") or "").strip()
    if not slug:
        raise ValueError("manifest.slug is required")

    post_slug = f"{publish_date.isoformat()}-{slug}"

    posts_dir = repo_root / "site" / "src" / "content" / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    post_path = posts_dir / f"{post_slug}.md"

    existing_md: str | None = None
    if post_path.exists():
        if not overwrite:
            raise FileExistsError(f"Post already exists (use overwrite): {post_path}")
        existing_md = post_path.read_text(encoding="utf-8")

    if post_path.exists() and not overwrite:
        raise FileExistsError(f"Post already exists (use overwrite): {post_path}")

    md = post_src_path.read_text(encoding="utf-8").rstrip() + "\n"
    if existing_md is not None:
        md = _preserve_existing_product_images(existing_md=existing_md, new_md=md)

    post_path.write_text(md, encoding="utf-8")

    pick_updated = 0
    pick_skipped = 0
    pick_errors: list[str] = []

    if enrich_pick_images and not dry_run:
        res = enrich_pick_images_for_markdown(
            markdown_path=post_path,
            slug=post_slug,
            repo_root=repo_root,
            allow_yaml_frontmatter_rewrite=True,
        )
        pick_updated = res.picks_updated
        pick_skipped = res.picks_skipped
        pick_errors = list(res.errors)

    # Ensure hero assets exist and inject missing frontmatter keys.
    public_dir = repo_root / "site" / "public"
    public_dir.mkdir(parents=True, exist_ok=True)

    placeholder_url = "/images/placeholder-hero.webp"

    # Only attempt regen if we have an API key and caller allows it.
    should_regen = (
        bool(os.environ.get("OPENAI_API_KEY"))
        and regen_hero_if_possible
        and not dry_run
    )

    if should_regen:
        # Lazy-import only if actually needed.
        from pipeline.image_step import generate_hero_image

        # Minimal inputs for prompt quality; safe fallbacks.
        fm = _extract_frontmatter(post_path.read_text(encoding="utf-8"))
        title = str(fm.get("title") or post_slug)
        category = None
        cats = fm.get("categories")
        if isinstance(cats, list) and cats:
            category = str(cats[0])

        # Use picks bodies if present.
        pick_snippets: list[str] = []
        picks = fm.get("picks")
        if isinstance(picks, list):
            for p in picks[:8]:
                if isinstance(p, dict):
                    body = str(p.get("body") or "").strip()
                    if body:
                        pick_snippets.append(body[:240])

        if not pick_snippets:
            pick_snippets = [title]

        hero_paths_obj = ensure_hero_assets_exist(
            public_dir=public_dir,
            slug=post_slug,
            placeholder_url=placeholder_url,
            regen_fn=generate_hero_image,
            regen_kwargs={
                "slug": post_slug,
                "category": category,
                "title": title,
                "intro": "",
                "picks": pick_snippets,
                "alternatives": None,
                "public_dir": public_dir,
            },
        )
    else:
        hero_paths_obj = ensure_hero_assets_exist(
            public_dir=public_dir,
            slug=post_slug,
            placeholder_url=placeholder_url,
            regen_fn=None,
            regen_kwargs=None,
        )

    # Inject hero keys if missing.
    hero_updates = {
        "heroImage": hero_paths_obj.hero,
        "heroImageHome": hero_paths_obj.hero_home,
        "heroImageCard": hero_paths_obj.hero_card,
        "heroImageSource": hero_paths_obj.hero_source,
        "heroAlt": f"{(_extract_frontmatter(post_path.read_text(encoding='utf-8')).get('title') or post_slug)} hero image",
    }

    md2 = _inject_missing_frontmatter_scalars(post_path.read_text(encoding="utf-8"), hero_updates)
    post_path.write_text(md2, encoding="utf-8")

    return HydrationResult(
        post_slug=post_slug,
        post_path=post_path,
        package_dir=package_dir,
        hero_paths={
            "heroImage": hero_paths_obj.hero,
            "heroImageHome": hero_paths_obj.hero_home,
            "heroImageCard": hero_paths_obj.hero_card,
            "heroImageSource": hero_paths_obj.hero_source,
        },
        pick_images_updated=pick_updated,
        pick_images_skipped=pick_skipped,
        pick_image_errors=pick_errors,
    )
