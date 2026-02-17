import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const filePath = path.resolve("src/pages/posts/[...slug].astro");

test("guide pages provide a concrete sidebar slot for Quick picks", () => {
  const src = fs.readFileSync(filePath, "utf8");

  // Regression guard: using <Fragment slot="sidebar"> can fail to register the slot,
  // causing the layout fallback sidebar to render instead of Quick picks.
  assert.ok(
    !src.includes('<Fragment slot="sidebar">'),
    "Do not use <Fragment slot=\"sidebar\">; use an element with slot=\"sidebar\" instead."
  );

  assert.ok(
    /<\w+\s+slot="sidebar"/.test(src),
    "Expected an element with slot=\"sidebar\" so Quick picks renders in the layout aside."
  );

  // Astro slotting can be picky if the slotted element is nested inside certain
  // conditional branches/fragments. Keep the sidebar slot at the same indentation
  // level as other PostLayout children.
  assert.ok(
    src.includes("\n    <div slot=\"sidebar\">"),
    "Expected `<div slot=\"sidebar\">` to be a direct PostLayout child (4-space indent)."
  );

  assert.ok(
    src.includes("Quick picks"),
    "Expected sidebar content to include Quick picks UI"
  );
});
