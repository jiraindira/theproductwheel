from agents.topic_agent import TopicSelectionAgent
from agents.product_agent import ProductDiscoveryAgent
from schemas.topic import TopicInput
from datetime import date
from pathlib import Path
import json
import re


ASTRO_POSTS_DIR = Path("site/src/content/posts")
LOG_PATH = Path("output/posts_log.json")


def slugify(text: str) -> str:
    # Lowercase, replace spaces with hyphens, remove unsafe characters
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
        product_models = product_agent.run(topic)  # list[Product]
        print(f"✅ {len(product_models)} products generated")
    except Exception as e:
        print("Error generating products:", e)
        return

    # 3) Filter + normalize + convert to JSON-safe dicts
            "url": str(p.url),  # IMPORTANT: HttpUrl -> str for YAML frontmatter (markdown) serialization
        {
            "title": normalize_text(p.title),
            "url": str(p.url),  # IMPORTANT: HttpUrl -> str for JSON/YAML safety
            "price": p.price,
            "rating": float(p.rating),
            "reviews_count": int(p.reviews_count),
            "description": normalize_text(p.description),
        }
        for p in product_models
        if p.rating >= 4.0 and p.reviews_count >= 250
    ]

    # Sort dicts (not pydantic models)
    products = sorted(
        products,
        key=lambda p: (p.get("rating", 0), p.get("reviews_count", 0)),
        reverse=True
    )

    if len(products) < 5:
        print("⚠️ Warning: fewer than 5 products passed filters.")

    # 4) File naming
    post_date = date.today().isoformat()
    slug = slugify(topic.topic)
    filename = f"{post_date}-{slug}.md"
    file_path = ASTRO_POSTS_DIR / filename

    # 5) Frontmatter must match site/src/content/config.ts
    # Schema requires: title, description, publishedAt, category, audience, products
    meta_description = f"Curated {topic.category.replace('_', ' ')} picks for {normalize_text(topic.audience)}."

    md = []
    md.append("---")
    md.append(f'title: "{normalize_text(topic.topic)}"')
    md.append(f'description: "{meta_description}"')
    md.append(f"publishedAt: {post_date}")
    md.append(f'category: "{topic.category}"')
    md.append(f'audience: "{normalize_text(topic.audience)}"')
    # Embed products as JSON inside YAML (valid YAML)
    md.append(f"products: {json.dumps(products, ensure_ascii=False)}")
    md.append("---")
    md.append("")
    md.append("## Why this list")
    md.append("")
    md.append(normalize_text(topic.rationale).strip())
    md.append("")
    # IMPORTANT: Do NOT render products in Markdown anymore if Astro renders cards from frontmatter.
    # Leaving the section out prevents duplication.

    file_path.write_text("\n".join(md), encoding="utf-8")
    print(f"✅ Astro post saved to {file_path}")

    # 6) Log
    append_log({
        "date": post_date,
        "title": normalize_text(topic.topic),
        "category": topic.category,
        "audience": normalize_text(topic.audience),
        "file": str(file_path).replace("\\", "/"),
        "product_count": len(products),
    })
    print(f"✅ Post logged in {LOG_PATH}")


if __name__ == "__main__":
    main()
