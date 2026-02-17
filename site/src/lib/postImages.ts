import type { ImageMetadata } from "astro";

const HERO_IMAGES = import.meta.glob("../assets/posts/**/hero.webp", {
  eager: true,
  import: "default",
}) as Record<string, ImageMetadata>;

function normalizePath(p: string) {
  return String(p)
    .replaceAll("\\", "/")
    .replace(/^\//, "")
    .replace(/^\.\//, "");
}

/**
 * Resolve the hero image metadata for a blog post from a frontmatter path.
 *
 * The `heroImagePath` is typically taken from frontmatter and may be specified
 * in several normalized forms. The following input formats are supported:
 *
 * - `"src/assets/posts/.../hero.webp"` (e.g. `src/assets/posts/my-post/hero.webp`)
 * - `"assets/posts/.../hero.webp"`    (e.g. `assets/posts/my-post/hero.webp`)
 *
 * The function normalizes path separators, strips leading `./`, `/`, and `src/`,
 * and matches the resulting path against the statically imported hero images
 * (which may have keys like `"../assets/posts/.../hero.webp"`). Matching is
 * done by suffix so that both `src/assets/...` and `assets/...` style paths
 * correctly resolve to the same underlying image.
 *
 * @param heroImagePath Path to a hero image as declared in frontmatter.
 * @returns The corresponding {@link ImageMetadata} if a matching hero image is
 *          found, or `null` if no matching image can be resolved.
 */
export function getPostHeroImage(heroImagePath: string): ImageMetadata | null {
  const wantedSuffix = normalizePath(heroImagePath)
    .replace(/^src\//, "")
    .replace(/^assets\//, "");

  for (const [key, mod] of Object.entries(HERO_IMAGES)) {
    const keyNorm = normalizePath(key)
      .replace(/^\.\.\//, "")
      .replace(/^src\//, "")
      .replace(/^assets\//, "");

    // The frontmatter uses `src/assets/...` while glob keys may look like `../assets/...`.
    // Match by suffix so both formats work.
    if (keyNorm.endsWith(wantedSuffix)) {
      return mod;
    }
  }

  return null;
}
