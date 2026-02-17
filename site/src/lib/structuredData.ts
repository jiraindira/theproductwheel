export type JsonLd = Record<string, unknown>;

export function toAbsoluteUrl(baseUrl: string, url: string): string {
  return new URL(url, baseUrl).toString();
}

export function buildBreadcrumbList(items: Array<{ name: string; url: string }>): JsonLd {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((it, idx) => ({
      "@type": "ListItem",
      position: idx + 1,
      name: it.name,
      item: it.url,
    })),
  };
}

export function buildArticleJsonLd(params: {
  canonicalUrl: string;
  headline: string;
  description?: string;
  imageUrl?: string;
  datePublished?: string;
  dateModified?: string;
  siteName: string;
  siteUrl: string;
  logoUrl?: string;
}): JsonLd {
  const {
    canonicalUrl,
    headline,
    description,
    imageUrl,
    datePublished,
    dateModified,
    siteName,
    siteUrl,
    logoUrl,
  } = params;

  const publisher: JsonLd = {
    "@type": "Organization",
    name: siteName,
    url: siteUrl,
    ...(logoUrl
      ? {
          logo: {
            "@type": "ImageObject",
            url: logoUrl,
          },
        }
      : {}),
  };

  return {
    "@context": "https://schema.org",
    "@type": "Article",
    mainEntityOfPage: {
      "@type": "WebPage",
      "@id": canonicalUrl,
    },
    headline,
    ...(description ? { description } : {}),
    ...(imageUrl ? { image: [imageUrl] } : {}),
    ...(datePublished ? { datePublished } : {}),
    ...(dateModified ? { dateModified } : {}),
    publisher,
  };
}

export function buildCollectionPageJsonLd(params: {
  canonicalUrl: string;
  name: string;
  description?: string;
  itemList: Array<{ name: string; url: string }>;
}): JsonLd {
  const { canonicalUrl, name, description, itemList } = params;

  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name,
    ...(description ? { description } : {}),
    url: canonicalUrl,
    mainEntity: {
      "@type": "ItemList",
      itemListOrder: "https://schema.org/ItemListOrderDescending",
      numberOfItems: itemList.length,
      itemListElement: itemList.map((it, idx) => ({
        "@type": "ListItem",
        position: idx + 1,
        url: it.url,
        name: it.name,
      })),
    },
  };
}
