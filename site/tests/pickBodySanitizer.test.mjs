import test from "node:test";
import assert from "node:assert/strict";

import { stripRedundantLeadingTitleBlock } from "../src/lib/pickBodySanitizer.mjs";

test("keeps real first paragraph that starts with the title", () => {
  const title = "Dreamon Take Apart Dinosaur Toys for Kids";
  const html =
    "<p>Dreamon Take Apart Dinosaur Toys for Kids earns a spot here because it turns another dinosaur into an activity.</p>" +
    "<p>Skip it if you hate small parts.</p>";

  const out = stripRedundantLeadingTitleBlock(html, title);
  assert.ok(out.includes("earns a spot"));
  assert.ok(out.includes("Skip it"));
});

test("removes a redundant one-line title echo paragraph", () => {
  const title = "Lehoo - Montessori Educational Construction Toy";
  const html = "<p>Montessori Educational Construction Toy</p><p>Real content here.</p>";
  const out = stripRedundantLeadingTitleBlock(html, title);
  assert.ok(!out.includes("Montessori Educational Construction Toy</p><p>"));
  assert.ok(out.includes("Real content here"));
});

test("removes a leading ul/li stray tagline that is a subset of the title", () => {
  const title = "ORSEN LCD Writing Tablet - Dinosaur Drawing Pad for Kids";
  const html = "<ul><li>Dinosaur Drawing Pad for Kids</li></ul><p>The ORSEN LCD Writing Tablet fits this guide.</p>";
  const out = stripRedundantLeadingTitleBlock(html, title);
  assert.ok(!out.includes("<li>Dinosaur Drawing Pad for Kids</li>"));
  assert.ok(out.includes("fits this guide"));
});

test("does not remove a real multi-item list", () => {
  const title = "Some Product";
  const html = "<ul><li>First point</li><li>Second point</li></ul><p>Body</p>";
  const out = stripRedundantLeadingTitleBlock(html, title);
  assert.ok(out.includes("<li>First point</li>"));
  assert.ok(out.includes("<li>Second point</li>"));
});
