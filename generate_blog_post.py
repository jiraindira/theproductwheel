from agents.topic_agent import TopicSelectionAgent
from agents.product_agent import ProductDiscoveryAgent
from agents.title_optimization_agent import TitleOptimizationAgent
from agents.depth_expansion_agent import DepthExpansionAgent

from schemas.topic import TopicInput
from schemas.title import TitleOptimizationInput
from schemas.depth import DepthExpansionInput, ExpansionModuleSpec

from datetime import date
from pathlib import Path
import json
import re
import shutil


ASTRO_POSTS_DIR = Path("site/src/content/posts")
LOG_PATH = Path("output/posts_log.json")

# Image convention (public/)
PUBLIC_IMAGES_DIR = Path("site/public/images")
PUBLIC_POST_IMAGES_DIR = PUBLIC_IMAGES_DIR / "posts"
PLACEHOLDER_HERO_PATH = PUBLIC_IMAGES_DIR / "placeholder-hero.webp"

# If you *do* have image credit info, set these.
# Otherwise leave as None and the generator will omit the fields entirely.
DEFAULT_IMAGE_CREDIT_NAME = None  # e.g. "Unsplash"
DEFAULT_IMAGE_CREDIT_URL = None   # e.g. "https://unsplash.com/photos/abc123"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^a-z0-9\-]", "", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")


NORMALIZE_TRANSLATION_TABLE = str.maketrans({
    "’": "'",
    "“": '"',
    "”": '"',
    "–": "-",
    "—": "-",
})


def normalize_text(s: str) -> str:
    return s.translate(NORMALIZE_TRANSLATION_TABLE)


def ensure_log_file():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        LOG_PATH.write_text("[]", encoding="utf-8")


def append_log(entry: dict):
    ensure_log_file()
    try:
        data = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            data = []
    except Exception:
        data = []
    data.append(entry)
    LOG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ensure_hero_image(slug: str) -> tuple[str, str]:
    """
    Guarantees hero image exists for this post.

    Contract:
      - File must exist at: site/public/images/posts/<slug>/hero.webp
      - Frontmatter should reference: /images/posts/<slug>/hero.webp

    If missing, copy placeholder-hero.webp into the folder.
    Returns (hero_image_url, hero_alt).
    """
    PUBLIC_POST_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    post_img_dir = PUBLIC_POST_IMAGES_DIR / slug
    post_img_dir.mkdir(parents=True, exist_ok=True)

    hero_file = post_img_dir / "hero.webp"
    hero_url = f"/images/posts/{slug}/hero.webp"

    if hero_file.exists():
        return hero_url, "Hero image for the guide"

    if not PLACEHOLDER_HERO_PATH.exists():
        raise FileNotFoundError(
            f"Missing placeholder hero image at {PLACEHOLDER_HERO_PATH}. "
            "Add site/public/images/placeholder-hero.webp so the generator can auto-fill missing heroes."
        )

    shutil.copyfile(PLACEHOLDER_HERO_PATH, hero_file)
    return hero_url, "Placeholder hero image"


def estimate_word_count(text: str) -> int:
    return len((text or "").strip().split())


def main():
    print(">>> generate_blog_post.py started")

    ASTRO_POSTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Topic
    topic_agent = TopicSelectionAgent()
    input_data = TopicInput(current_date=date.today().isoformat(), region="US")

    try:
        topic = topic_agent.run(input_data)
        print("✅ Topic generated:", topic.topic)
    except Exception as e:
        print("Error generating topic:", e)
        return

    # 2) Products
    product_agent = ProductDiscoveryAgent()
    try:
        product_models = product_agent.run(topic)
        print(f"✅ {len(product_models)} products generated")
    except Exception as e:
        print("Error generating products:", e)
        return

    # 3) Filter + normalize + convert to JSON-safe dicts
    products = [
        {
            "title": normalize_text(p.title),
            "url": str(p.url),
            "price": p.price,
            "rating": float(p.rating),
            "reviews_count": int(p.reviews_count),
            "description": normalize_text(p.description),
        }
        for p in product_models
        if float(p.rating) >= 4.0 and int(p.reviews_count) >= 250
    ]

    products = sorted(
        products,
        key=lambda p: (p.get("rating", 0), p.get("reviews_count", 0)),
        reverse=True,
    )

    if len(products) < 5:
        print("⚠️ Warning: fewer than 5 products passed filters.")

    # 4) Improve title (TitleOptimizationAgent)
    existing_titles: list[str] = []
    try:
        if LOG_PATH.exists():
            prior = json.loads(LOG_PATH.read_text(encoding="utf-8"))
            if isinstance(prior, list):
                existing_titles = [
                    normalize_text(x.get("title", ""))
                    for x in prior
                    if isinstance(x, dict) and x.get("title")
                ]
    except Exception:
        existing_titles = []

    title_agent = TitleOptimizationAgent()
    title_inp = TitleOptimizationInput(
        topic=normalize_text(topic.topic),
        primary_keyword=normalize_text(topic.topic),
        secondary_keywords=[],
        existing_titles=existing_titles,
        num_candidates=40,
        return_top_n=3,
        banned_starts=["Top", "Top Cozy", "Top cosy", "Best", "Best Cozy", "Best cosy"],
        voice="neutral",
    )

    title_out = title_agent.run(title_inp)
    selected_title = normalize_text(topic.topic)
    try:
        if title_out.get("selected"):
            selected_title = title_out["selected"][0]["title"]
    except Exception:
        selected_title = normalize_text(topic.topic)

    print("✅ Selected title:", selected_title)

    # 5) File naming
    post_date = date.today().isoformat()
    slug = slugify(selected_title)
    filename = f"{post_date}-{slug}.md"
    file_path = ASTRO_POSTS_DIR / filename

    # 6) Hero image
    post_slug = f"{post_date}-{slug}"
    try:
        hero_image_url, hero_alt = ensure_hero_image(post_slug)
    except Exception as e:
        print("❌ Hero image guard failed:", e)
        return

    # 7) Frontmatter must match site/src/content/config.ts
    meta_description = f"Curated {topic.category.replace('_', ' ')} picks for {normalize_text(topic.audience)}."

    md = []
    md.append("---")
    md.append(f'title: "{normalize_text(selected_title)}"')
    md.append(f'description: "{meta_description}"')
    md.append(f"publishedAt: {post_date}")
    md.append(f'category: "{topic.category}"')
    md.append(f'audience: "{normalize_text(topic.audience)}"')

    md.append(f'heroImage: "{hero_image_url}"')
    md.append(f'heroAlt: "{hero_alt}"')

    # ✅ Only include image credit fields if present.
    if DEFAULT_IMAGE_CREDIT_NAME:
        md.append(f'imageCreditName: "{DEFAULT_IMAGE_CREDIT_NAME}"')
    if DEFAULT_IMAGE_CREDIT_URL:
        md.append(f'imageCreditUrl: "{DEFAULT_IMAGE_CREDIT_URL}"')

    # Products as JSON inside YAML (valid YAML)
    md.append(f"products: {json.dumps(products, ensure_ascii=False)}")
    md.append("---")
    md.append("")
    md.append("## Why this list")
    md.append("")
    md.append(normalize_text(topic.rationale).strip())
    md.append("")

    draft_markdown = "\n".join(md)
    before_wc = estimate_word_count(draft_markdown)

    # 8) Depth expansion
    depth_agent = DepthExpansionAgent()
    depth_inp = DepthExpansionInput(
        topic=normalize_text(topic.topic),
        primary_keyword=normalize_text(topic.topic),
        secondary_keywords=[],
        title=normalize_text(selected_title),
        slug=post_slug,
        draft_markdown=draft_markdown,
        products=products,
        outline=[],
        faqs=[],
        target_word_count=1400,
        max_added_words=1200,
        voice="neutral",
        modules=[
            ExpansionModuleSpec(name="quick_picks", enabled=True, max_words=220),
            ExpansionModuleSpec(name="how_we_chose", enabled=True, max_words=220),
            ExpansionModuleSpec(name="buyers_guide", enabled=True, max_words=450),
            ExpansionModuleSpec(name="faqs", enabled=True, max_words=420),
            ExpansionModuleSpec(name="alternatives", enabled=True, max_words=280),
            ExpansionModuleSpec(name="care_and_maintenance", enabled=True, max_words=280),
        ],
        forbid_claims_of_testing=True,
        allow_new_sections=True,
        render_products_in_body=False,
    )

    depth_out = depth_agent.run(depth_inp)
    final_markdown = depth_out.get("expanded_markdown", draft_markdown)
    after_wc = estimate_word_count(final_markdown)

    # 9) Write post
    file_path.write_text(final_markdown, encoding="utf-8")
    print(f"✅ Astro post saved to {file_path}")

    # 10) Log
    append_log({
        "date": post_date,
        "title": normalize_text(selected_title),
        "topic": normalize_text(topic.topic),
        "category": topic.category,
        "audience": normalize_text(topic.audience),
        "file": str(file_path).replace("\\", "/"),
        "product_count": len(products),
        "heroImage": hero_image_url,
        "word_count_before": before_wc,
        "word_count_after": after_wc,
        "depth_modules_applied": depth_out.get("applied_modules", []),
        "title_candidates_top3": (title_out.get("selected", [])[:3] if isinstance(title_out, dict) else []),
    })
    print(f"✅ Post logged in {LOG_PATH}")


if __name__ == "__main__":
    main()
