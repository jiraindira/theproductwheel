// @ts-check
import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";

import { wrapMethodologyCallout } from "./src/lib/remark/wrapMethodologyCallout.ts";

console.log("[astro.config] methodology plugin is", typeof wrapMethodologyCallout);

export default defineConfig({
  site:
    process.env.SITE_URL ??
    (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : "http://localhost:4321"),
  integrations: [tailwind()],
  markdown: {
    // wrappers first (no injectors)
    remarkPlugins: [wrapMethodologyCallout],
  },
});
