import { getEntry } from "astro:content";

export type Taxonomy = {
  brand: { name: string; tagline: string };
  groups: { key: string; label: string; intro: string; categories: string[] }[];
};

export async function getTaxonomy(): Promise<Taxonomy> {
  const entry = await getEntry("site", "taxonomy");
  if (!entry) throw new Error("Missing site taxonomy: src/content/site/taxonomy.json");
  return entry.data as Taxonomy;
}

export function prettyCategory(s: string) {
  if (!s) return "";
  return s
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/\bAnd\b/g, "&");
}

export function groupForCategory(taxonomy: Taxonomy, category: string) {
  const g = taxonomy.groups.find((x) => x.categories.includes(category));
  return g ? { key: g.key, label: g.label, intro: g.intro } : { key: "other", label: "Other", intro: "" };
}
