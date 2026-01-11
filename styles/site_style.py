from __future__ import annotations

from typing import Dict, List, TypedDict


class QuickPickRule(TypedDict):
    keywords: List[str]
    one_liner: str


class StyleProfile(TypedDict):
    name: str
    tone: str

    # Short excerpt that represents your “north star” voice.
    # Used as a style reference for LLM writing (not copied verbatim).
    golden_post_excerpt: str

    banned_phrases: List[str]
    forbidden_terms: List[str]
    preferred_terms: List[str]

    # Deterministic fallbacks (used in repair/preserve, or when LLM disabled)
    why_this_list_body: str
    quick_picks_intro_lines: List[str]
    how_we_chose_intro: str
    how_we_chose_bullets: List[str]

    quick_pick_rules: List[str]
    quick_pick_keyword_rules: List[QuickPickRule]

    buyers_guide_intro: str
    buyers_guide_questions: List[str]

    faq_intro: str
    faq_seeds: List[str]
    faq_answers: Dict[str, str]
    faq_default_answer: str

    alternatives_intro: str
    alternatives_tips: List[str]

    care_intro: str
    care_tips: List[str]


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def _map_category(category: str) -> str:
    c = _norm(category)

    canonical = {
        "technology",
        "home_and_kitchen",
        "health_and_fitness",
        "beauty_and_grooming",
        "outdoors_and_travel",
        "parenting_and_family",
        "finance_and_productivity",
        "food_and_cooking",
        "pets",
        "fashion",
        "general",
    }
    if c in canonical:
        return c

    if "parent" in c or "baby" in c or "family" in c:
        return "parenting_and_family"
    if "outdoor" in c or "travel" in c or "camp" in c or "hike" in c or "adventure" in c:
        return "outdoors_and_travel"
    if "tech" in c or "gadget" in c or "electronics" in c:
        return "technology"
    if "kitchen" in c or "home" in c or "appliance" in c:
        return "home_and_kitchen"
    if "health" in c or "fitness" in c or "workout" in c or "wellness" in c or "supplement" in c:
        return "health_and_fitness"
    if "beauty" in c or "groom" in c or "skincare" in c or "hair" in c:
        return "beauty_and_grooming"
    if "finance" in c or "money" in c or "budget" in c or "productivity" in c:
        return "finance_and_productivity"
    if "food" in c or "cook" in c or "recipe" in c:
        return "food_and_cooking"
    if "pet" in c or "dog" in c or "cat" in c:
        return "pets"
    if "fashion" in c or "clothing" in c or "apparel" in c or "shoe" in c:
        return "fashion"

    return "general"


# Generic “north star” excerpt that works for any category.
_GOLDEN_GENERIC = (
    "I used to think buying “the right one” was a personality trait. Then I tried to buy a simple thing, "
    "fell into a 37-tab rabbit hole, and emerged two hours later with a cart full of regret and one very specific "
    "question: why is everything either junk or suspiciously expensive?\n\n"
    "So this guide is for the version of us who wants something that works, fits into real life, and doesn’t become "
    "another object we silently resent. We’re looking for the boring kind of great: easy to use, not fussy to maintain, "
    "and genuinely helpful on a Tuesday."
)


def _base_profile(name: str, tone: str) -> StyleProfile:
    return {
        "name": name,
        "tone": tone,

        "golden_post_excerpt": _GOLDEN_GENERIC,

        "banned_phrases": ["top", "ultimate", "best ever", "category rotation", "affiliate market"],
        "forbidden_terms": [],
        "preferred_terms": [],

        "why_this_list_body": (
            "This guide is meant to reduce regret. We focus on practical picks with clear benefits, and we avoid vague "
            "promises. Think: fewer surprises after you buy."
        ),

        "quick_picks_intro_lines": [
            "If you’re short on time, start here.",
            "These are the picks that tend to earn their keep in real life:",
        ],

        "how_we_chose_intro": "We prioritized choices that are practical and easy to live with.",
        "how_we_chose_bullets": [
            "Clear benefits over marketing buzzwords",
            "Ease of use and low maintenance",
            "Durability and fewer returns",
            "Value: worth the space and the money",
        ],

        "quick_pick_rules": [
            "Each pick should include: what it is + why it helps + one practical note.",
            "Avoid generic praise. Say something concrete.",
        ],
        "quick_pick_keyword_rules": [],

        "buyers_guide_intro": "A few quick questions usually get you to the right choice:",
        "buyers_guide_questions": [
            "Where will you use it most?",
            "What constraints matter (budget, space, maintenance)?",
            "Do you prefer simple or feature-rich?",
        ],

        "faq_intro": "A few questions that come up a lot:",
        "faq_seeds": ["How do I choose the right option?"],
        "faq_answers": {},
        "faq_default_answer": (
            "Start with where you’ll use it most and what annoys you today. Then choose the simplest option that solves "
            "that problem without creating extra hassle."
        ),

        "alternatives_intro": "If you want to adjust for budget or preferences:",
        "alternatives_tips": [
            "A lower-cost version if you’re unsure you’ll use it often",
            "A higher-end pick if durability or comfort matters most",
        ],

        "care_intro": "A little upkeep goes a long way:",
        "care_tips": [
            "Keep packaging until you’re sure you’ll keep it (returns are easier).",
            "Follow manufacturer instructions for cleaning and storage.",
        ],
    }


def get_style_profile(category: str, voice: str = "neutral") -> StyleProfile:
    cat = _map_category(category)
    profiles: Dict[str, StyleProfile] = {}

    # -------------------------
    # HEALTH & FITNESS (UPGRADED)
    # -------------------------
    h = _base_profile("Wellness Winter Journal Voice", "journal")
    h.update({
        "golden_post_excerpt": (
            _GOLDEN_GENERIC
            + "\n\n"
            + "Winter wellness shopping has the special energy of a late-night airport snack run: you’re tired, "
              "you want a quick fix, and somehow you’re holding something you didn’t mean to buy. The trick is to keep it "
              "boring on purpose. Clear labels. Sensible servings. Stuff you’ll actually take."
        ),
        "banned_phrases": h["banned_phrases"] + [
            "immune-boosting", "boost your immunity", "prevent colds", "cure",
        ],
        "forbidden_terms": [
            "cure", "guaranteed", "prevent covid", "treat disease", "miracle",
            "clinically proven to prevent", "doctor-approved (unless sourced)",
        ],
        "preferred_terms": [
            "supports immune function",
            "winter routine",
            "evidence-informed",
            "third-party testing",
            "NSF",
            "USP",
            "dosage",
            "form factor",
            "interactions",
            "talk to your clinician",
            "consistent",
        ],
    })
    profiles["health_and_fitness"] = h

    # -------------------------
    # Other categories (safe defaults, now with golden voice anchor)
    # -------------------------
    profiles["beauty_and_grooming"] = _base_profile("Beauty Real-Life Journal Voice", "journal")
    profiles["technology"] = _base_profile("Tech Buyer Journal Voice", "journal")
    profiles["home_and_kitchen"] = _base_profile("Home Practical Journal Voice", "journal")
    profiles["outdoors_and_travel"] = _base_profile("Outdoors Journal Voice", "journal")
    profiles["parenting_and_family"] = _base_profile("Parenting Journal Voice", "journal")
    profiles["finance_and_productivity"] = _base_profile("Finance/Productivity Practical Voice", "journal")
    profiles["food_and_cooking"] = _base_profile("Cooking Cozy Journal Voice", "journal")
    profiles["pets"] = _base_profile("Pets Warm Practical Voice", "journal")
    profiles["fashion"] = _base_profile("Fashion Real-Life Voice", "journal")
    profiles["general"] = _base_profile("General Practical Voice", "practical")

    return profiles.get(cat, profiles["general"])
