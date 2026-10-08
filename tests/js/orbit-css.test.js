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

test("the dock never cuts its lesson off: it grows up to half the window, then scrolls as a whole", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(rule(".dock"), /max-height: 50vh;\s*overflow-y: auto;/);
  assert.doesNotMatch(rule(".dock-lesson"), /max-height|overflow/);
});

test("buttons and small labels use the readable text face in bold, and headings keep the pixel face", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.equal(tokens(css, ":root")["--f-ui"], "var(--f-body)");
  for (const selector of [".btn", ".counter", ".snum", ".card-num", ".comms-who", ".cs-who"]) assert.match(rule(selector), /font: 700 [^;]*var\(--f-ui\)/, selector);
  for (const selector of [".map-title", ".sector h2", ".card-title", ".band h2", ".dock-title"]) assert.match(rule(selector), /var\(--f-px\)/, selector);
});

test("each rule appears once at the top level, so a later copy cannot silently override it", () => {
  const top = [];
  let depth = 0;
  let text = "";
  for (const char of css.replace(/\/\*[\s\S]*?\*\//g, "")) {
    if (char === "{" && depth++ === 0) top.push(text.trim());
    if (char === "{" || char === "}") text = "";
    else text += char;
    if (char === "}") depth -= 1;
  }
  const repeated = top.filter((selector, index) => top.indexOf(selector) !== index && !selector.startsWith("@"));
  assert.deepEqual([...new Set(repeated)].sort(), ["*,\n*::before,\n*::after", ".termcol"]);
});

test("a conflicted file shows the crack icon in place of its status square", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(rule('.file[data-state="conflicted"]::before'), /display: none;/);
});

test("a prediction's choice reads as one line of text, its commands inline, never in columns", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(rule(".goal-choice"), /display: block;/);
});

test("Alex's mirrored station draws at about 60 percent and takes no clicks, so your zones keep the room", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(rule(".station.is-mirror"), /zoom: 0\.6;/);
  assert.match(rule(".station.is-mirror"), /pointer-events: none;/);
  assert.match(rule(".viz-crew"), /grid-template-columns: minmax\(0, 1fr\) minmax\(150px, 200px\) minmax\(0, 0\.6fr\);/);
});
