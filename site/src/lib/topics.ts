// src/lib/topics.ts
import fs from "node:fs";
import path from "node:path";

export const ALLOWED_CATEGORIES = [
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
] as const;

export type CategorySlug = (typeof ALLOWED_CATEGORIES)[number];

function normalizeLine(line: string) {
  // allow "home_and_kitchen", "Home and Kitchen", "home-and-kitchen"
  return line
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_")
    .replace(/[^\w_]/g, "");
}

export function prettyCategory(slug: string) {
  return slug
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/\bAnd\b/g, "&");
}

function isAllowed(slug: string): slug is CategorySlug {
  return (ALLOWED_CATEGORIES as readonly string[]).includes(slug);
}

/**
 * Reads topic_selection.txt and returns an ordered list of allowed category slugs.
 * - Ignores blank lines and comments (# ...)
 * - Normalizes common formatting
 * - If file missing or yields nothing, falls back to all allowed categories
 */
export function getSelectedTopics(): CategorySlug[] {
  // Adjust paths here if your topic_selection.txt lives elsewhere.
  // Common options:
  // - project root: <repo>/site/topic_selection.txt
  // - src/data/topic_selection.txt
  const candidatePaths = [
    path.join(process.cwd(), "topic_selection.txt"),
    path.join(process.cwd(), "src", "data", "topic_selection.txt"),
  ];

  let raw = "";
  for (const p of candidatePaths) {
    if (fs.existsSync(p)) {
      raw = fs.readFileSync(p, "utf8");
      break;
    }
  }

  if (!raw) {
    return [...ALLOWED_CATEGORIES];
  }

  const lines = raw
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith("#"));

  const picked: CategorySlug[] = [];
  for (const line of lines) {
    const slug = normalizeLine(line);
    if (isAllowed(slug) && !picked.includes(slug)) picked.push(slug);
  }

  return picked.length ? picked : [...ALLOWED_CATEGORIES];
}
