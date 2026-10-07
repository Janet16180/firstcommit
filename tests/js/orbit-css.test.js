"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const { STATIC } = require("./load");

const css = fs.readFileSync(path.join(STATIC, "orbit.css"), "utf8");
const design = fs.readFileSync(path.join(STATIC, "..", "..", "..", "..", "docs", "drafts", "orbit-design.html"), "utf8");

/* The custom properties a rule block sets, by name. */
function tokens(source, selector) {
  const start = source.indexOf(`${selector}{`) >= 0 ? source.indexOf(`${selector}{`) : source.indexOf(`${selector} {`);
  const block = source.slice(source.indexOf("{", start) + 1, source.indexOf("}", start));
  return Object.fromEntries([...block.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)].map((match) => [match[1], match[2].trim()]));
}

test("the light look has the design's colour tokens, with the design's values", () => {
  const ours = tokens(css, ":root");
  const theirs = tokens(design, ":root");
  for (const name of Object.keys(theirs).filter((key) => !key.startsWith("--f-"))) assert.equal(ours[name], theirs[name], name);
});

test("the dark look has the design's dark tokens, with the design's values", () => {
  const ours = tokens(css, ':root[data-theme="dark"]');
  const theirs = tokens(design, ':root[data-theme="dark"]');
  assert.ok(Object.keys(theirs).length > 10);
  for (const [name, value] of Object.entries(theirs)) assert.equal(ours[name], value, name);
});

test("the older views' tokens are mapped onto the design's, so every view wears one palette", () => {
  const ours = tokens(css, ":root");
  for (const name of ["--sans", "--surface", "--surface-2", "--muted", "--accent", "--focus"]) assert.match(ours[name], /^var\(--/, name);
});

test("the fonts are Tiny5 for headings and the design's text and terminal fonts, and nothing is loaded from the network", () => {
  const ours = tokens(css, ":root");
  assert.match(ours["--f-px"], /^'Tiny5'/);
  assert.match(ours["--f-body"], /^'Atkinson Hyperlegible'/);
  assert.match(ours["--f-term"], /^'VT323'/);
  assert.doesNotMatch(css, /url\(|@import|https?:/);
});

test("no typed symbol stands in for a picture", () => {
  assert.doesNotMatch(css, /content:\s*"[^"]+"/);
  assert.doesNotMatch(css, /[☀-➿⭐\u{1F000}-\u{1FFFF}]/u);
});

test("the motions stop for players who ask for reduced motion", () => {
  const reduced = css.slice(css.indexOf("@media (prefers-reduced-motion: reduce)"));
  for (const name of [".band-veil", ".band", ".dock"]) assert.ok(reduced.includes(name), name);
});

test("ligatures are off on every element, so a pixel font never joins fi or fl into one glyph", () => {
  assert.match(css, /\*,\s*\*::before,\s*\*::after\s*{\s*font-variant-ligatures:\s*none\s*!important;\s*}/);
});

test("the terminal's column reaches the bottom of the window, with a minimum height, and its terminal fills it", () => {
  assert.match(css, /\.termcol {\s*height: max\(var\(--term-min\), calc\(100vh - var\(--term-top/);
  assert.match(tokens(css, ":root")["--term-min"], /^\d+px$/);
  assert.match(css, /\.termcol \.term-host,[^{]*{[^}]*flex: 1;[^}]*height: auto !important;/);
});
