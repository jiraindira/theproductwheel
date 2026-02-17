import type { APIRoute } from "astro";
import { getCollection } from "astro:content";

const xmlEscape = (s: string) =>
  s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");

export const GET: APIRoute = async ({ site }) => {
  const base = (site ?? new URL("http://localhost")).toString().replace(/\/$/, "");

  const posts = await getCollection("posts");
  const postUrls = posts
    .slice()
    .sort((a, b) => b.data.publishedAt.getTime() - a.data.publishedAt.getTime())
    .map((p) => ({
      loc: `${base}/posts/${p.slug}`,
      lastmod: p.data.publishedAt.toISOString(),
    }));

  const staticUrls = [
    { loc: `${base}/`, lastmod: undefined },
    { loc: `${base}/posts`, lastmod: undefined },
    { loc: `${base}/cookies`, lastmod: undefined },
  ];

  const all = [...staticUrls, ...postUrls];

  const body = `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    all
      .map((u) => {
        const loc = `<loc>${xmlEscape(u.loc)}</loc>`;
        const lastmod = u.lastmod ? `\n    <lastmod>${xmlEscape(u.lastmod)}</lastmod>` : "";
        return `  <url>\n    ${loc}${lastmod}\n  </url>`;
      })
      .join("\n") +
    `\n</urlset>\n`;

  return new Response(body, {
    headers: {
      "Content-Type": "application/xml; charset=utf-8",
    },
  });
};
