import { visit } from "unist-util-visit";

/**
 * Wraps a "How this list was chosen" style section
 * in a semantic <aside> methodology callout.
 */
export function wrapMethodologyCallout() {
  const MATCHERS = [
    /^how this list was chosen$/i,
    /^how we chose$/i,
    /^how we picked$/i,
    /^our methodology$/i,
  ];

  return (tree) => {
    const children = tree.children;
    if (!Array.isArray(children)) return;

    let startIndex = -1;
    let startDepth = null;

    for (let i = 0; i < children.length; i++) {
      const node = children[i];
      if (node.type !== "heading") continue;

      const text = extractText(node);
      if (!text) continue;

      if (MATCHERS.some((re) => re.test(text.trim()))) {
        startIndex = i;
        startDepth = node.depth;
        break;
      }
    }

    if (startIndex === -1) return;

    let endIndex = children.length;
    for (let i = startIndex + 1; i < children.length; i++) {
      const node = children[i];
      if (node.type === "heading" && node.depth <= startDepth) {
        endIndex = i;
        break;
      }
    }

    const section = children.slice(startIndex, endIndex);

    const open = {
      type: "html",
      value:
        '<aside class="callout callout--methodology" aria-label="How this list was chosen">',
    };

    const close = {
      type: "html",
      value: "</aside>",
    };

    children.splice(startIndex, endIndex - startIndex, open, ...section, close);
  };
}

function extractText(heading) {
  let out = "";
  for (const child of heading.children || []) {
    if (child.type === "text") out += child.value;
    if (child.type === "inlineCode") out += child.value;
  }
  return out;
}
