import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

function run(cmd, args, options = {}) {
  const cwd = options.cwd ?? process.cwd();
  const stdio = options.stdio ?? "inherit";
  const env = { ...process.env, ...(options.env ?? {}) };

  // Windows: prefer cmd.exe to reliably invoke npm/yarn/pnpm shims.
  const isWin = process.platform === "win32";
  const needsQuotes = (s) => /\s|"/.test(String(s));
  const q = (s) => (needsQuotes(s) ? `"${String(s).replaceAll('"', '\\"')}"` : String(s));

  const result = isWin
    ? spawnSync("cmd.exe", ["/d", "/s", "/c", [cmd, ...args].map(q).join(" ")], {
        cwd,
        stdio,
        env,
        windowsHide: true,
      })
    : spawnSync(cmd, args, { cwd, stdio, env });

  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`Command failed (${result.status}): ${cmd} ${args.join(" ")}`);
  }
}

// Build once for this test file (slower, but validates what ships).
run("npm", ["run", "build"], { cwd: path.resolve(".") });

function readDist(relPath) {
  const p = path.resolve("dist", relPath);
  assert.ok(fs.existsSync(p), `Expected built file to exist: ${p}`);
  return fs.readFileSync(p, "utf8");
}

test("guide pages render Quick picks in the sidebar (not fallback TOC)", () => {
  const html = readDist("posts/2026-01-31-travel-rain-gear-essentials/index.html");

  assert.ok(html.includes("Quick picks"), "Expected Quick picks to render in built HTML");
  assert.ok(html.includes("sidecard-lite"), "Expected Quick picks card markup in sidebar");

  // The layout fallback sidebar contains "On this page".
  assert.ok(
    !html.includes("On this page"),
    "Did not expect fallback TOC sidebar to render when Quick picks slot is provided"
  );

  // Guard: Quick pick links should be unique and point at real IDs.
  const start = html.indexOf('<ol class="quick-list"');
  const end = start >= 0 ? html.indexOf("</ol>", start) : -1;
  assert.ok(start >= 0 && end > start, "Expected Quick picks list markup to exist");

  const quickListHtml = html.slice(start, end);
  const hrefs = [...quickListHtml.matchAll(/href=\"#([^\"]+)\"/g)].map((m) => m[1]);
  assert.ok(hrefs.length > 0, "Expected at least one Quick picks link");

  const unique = new Set(hrefs);
  assert.equal(unique.size, hrefs.length, "Expected Quick picks anchors to be unique");

  for (const id of hrefs) {
    assert.ok(html.includes(`id=\"${id}\"`), `Expected an element id=\"${id}\" in the page`);
  }
});

test("thought pieces do not render guide sidebar UI", () => {
  const html = readDist(
    "posts/2026-02-08-dehumidified-is-not-just-dry-why-moisture-control-matters/index.html",
  );

  // Article mode: no guide sidebar.
  assert.ok(!html.includes("Quick picks"), "Did not expect Quick picks on thought pieces");
  assert.ok(!html.includes("On this page"), "Did not expect TOC sidebar fallback on thought pieces");
  assert.ok(
    !html.includes("Tip: skim the picks first"),
    "Did not expect guide sidebar tip text on thought pieces",
  );
});

test("pick bodies are not truncated and stray one-item list is removed", () => {
  const html = readDist("posts/2026-02-08-gifts-for-4-year-olds-top-10-birthday-gift-ideas/index.html");

  // Regression: first paragraph used to be stripped if it began with the product title.
  assert.ok(
    html.includes("earns a spot here because"),
    "Expected real first paragraph text to be present in built HTML"
  );

  // Regression: stray markdown like "- Dinosaur Drawing Pad for Kids" rendered as a one-item list.
  assert.ok(
    !html.includes("<li>Dinosaur Drawing Pad for Kids</li>"),
    "Did not expect a stray one-item list item to appear in built HTML"
  );
});
