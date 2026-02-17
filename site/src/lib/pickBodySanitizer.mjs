function normalizeText(s) {
  return String(s || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function stripHtmlTags(s) {
  return String(s || "")
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function decodeBasicEntities(s) {
  return String(s || "")
    .replaceAll("&nbsp;", " ")
    .replaceAll("&amp;", "&")
    .replaceAll("&quot;", '"')
    .replaceAll("&#39;", "'")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">")
    .trim();
}

function words(s) {
  const t = normalizeText(s);
  return t ? t.split(/\s+/).filter(Boolean) : [];
}

function isMostlyRedundantTitle(firstTextNorm, titleNorm) {
  if (!firstTextNorm || !titleNorm) return false;
  if (firstTextNorm === titleNorm) return true;

  const firstWords = words(firstTextNorm);
  const titleWords = words(titleNorm);

  // If the first block is *longer* than the title by a lot, it's not a redundant title echo.
  // (e.g. "<title> earns a spot because ..." should be kept)
  if (firstWords.length >= titleWords.length + 4) return false;

  // If most words are shared with the title, treat it as a redundant echo.
  const titleSet = new Set(titleWords);
  const shared = firstWords.filter((w) => titleSet.has(w)).length;
  const ratio = firstWords.length ? shared / firstWords.length : 0;

  // Also allow short subsets that clearly belong to the title.
  const subset = shared === firstWords.length && firstWords.length >= 3;

  return ratio >= 0.85 || subset;
}

/**
 * Removes a leading block that repeats the product title, but preserves real sentences.
 * Handles:
 * - <p>/<h3>/<h4> single block title echoes
 * - <ul>/<ol> with a single <li> title echo (common stray markdown like "- tagline")
 */
export function stripRedundantLeadingTitleBlock(html, titleText) {
  const raw = String(html || "").trim();
  if (!raw) return "";

  const titleNorm = normalizeText(titleText);

  // 1) Handle a leading UL/OL with a single LI.
  const listMatch = raw.match(/^\s*<(ul|ol)\b[^>]*>([\s\S]*?)<\/\1>\s*/i);
  if (listMatch) {
    const inner = listMatch[2] ?? "";
    const items = [...inner.matchAll(/<li\b[^>]*>([\s\S]*?)<\/li>/gi)].map((m) => m[1] ?? "");

    if (items.length === 1) {
      const liTextNorm = normalizeText(decodeBasicEntities(stripHtmlTags(items[0])));
      if (isMostlyRedundantTitle(liTextNorm, titleNorm)) {
        return raw.slice(listMatch[0].length).trim();
      }
    }
  }

  // 2) Handle a leading P/H3/H4.
  const blockMatch = raw.match(/^\s*<(p|h3|h4)\b[^>]*>([\s\S]*?)<\/\1>\s*/i);
  if (!blockMatch) return raw;

  const firstTextNorm = normalizeText(decodeBasicEntities(stripHtmlTags(blockMatch[2] ?? "")));

  if (isMostlyRedundantTitle(firstTextNorm, titleNorm)) {
    return raw.slice(blockMatch[0].length).trim();
  }

  return raw;
}
