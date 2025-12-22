from agents.topic_agent import TopicSelectionAgent
from agents.product_agent import ProductDiscoveryAgent
from schemas.topic import TopicInput
from datetime import date
from pathlib import Path
import json

def main():
    print(">>> generate_blog_post.py started")

    # 1️⃣ Generate Topic
    topic_agent = TopicSelectionAgent()
    input_data = TopicInput(current_date=date.today().isoformat(), region="US")
    try:
        topic = topic_agent.run(input_data)
        print("✅ Topic generated:", topic.topic)
    except Exception as e:
        print("Error generating topic:", e)
        return

    # 2️⃣ Generate Products
    product_agent = ProductDiscoveryAgent()
    try:
        products = product_agent.run(topic)
        print(f"✅ {len(products)} products generated")
    except Exception as e:
        print("Error generating products:", e)
        return

    # 3️⃣ Filter and Sort Products
    products = [p for p in products if p.rating >= 4.0 and p.reviews_count >= 250]
    if len(products) < 5:
        print("⚠️ Warning: fewer than 5 high-quality products generated.")
    products = sorted(products, key=lambda p: (p.rating, p.reviews_count), reverse=True)

    # 4️⃣ Create Markdown content with front-matter
    md_content = f"""---
title: {topic.topic}
date: {date.today().isoformat()}
audience: {topic.audience}
category: {topic.category}
---

# {topic.topic}

*Audience:* {topic.audience}  
*Category:* {topic.category}  
*Rationale:* {topic.rationale}

## Top Products:

"""
    for idx, p in enumerate(products, start=1):
        md_content += f"""### {idx}. {p.title}
- Price: {p.price}
- Rating: {p.rating}⭐ ({p.reviews_count} reviews)
- Link: {p.url}
- Description: {p.description}

"""

    # 5️⃣ Save Markdown file
    safe_topic = topic.topic.replace(" ", "_").replace("/", "-")
    output_path = Path("output")
    output_path.mkdir(exist_ok=True)
    filename = f"blog_{date.today().isoformat()}_{safe_topic}.md"
    file_path = output_path / filename

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"✅ Blog post saved to {file_path}")

    # 6️⃣ Log generated post
    log_path = Path("output/posts_log.json")
    log_path.parent.mkdir(exist_ok=True)
    if log_path.exists():
        try:
            log_data = json.loads(log_path.read_text(encoding="utf-8"))
        except Exception:
            log_data = []
    else:
        log_data = []

    log_entry = {
        "date": date.today().isoformat(),
        "topic": topic.topic,
        "category": topic.category,
        "filename": filename
    }
    log_data.append(log_entry)

    log_path.write_text(json.dumps(log_data, indent=2), encoding="utf-8")
    print(f"✅ Post logged in {log_path}")

if __name__ == "__main__":
    main()
