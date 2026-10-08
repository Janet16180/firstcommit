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

test("a long address in a zone's message wraps inside the zone", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(rule(".zone-empty code"), /white-space: normal;\s*overflow-wrap: anywhere;/);
});

test("a moment covers the zones where they stand, its picture filling them, until it is put away", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(rule(".views"), /grid-area: viz;/);
  assert.match(rule(".sky"), /position: relative;/);
  assert.match(rule(".moment-layer"), /position: absolute;/);
  assert.match(rule(".moment-layer"), /inset: 0;/);
  assert.match(rule(".moment-layer .art-moment"), /width: 100%;/);
  assert.match(rule(".moment-layer .art-moment"), /height: 100%;/);
  assert.match(rule(".moment-layer[hidden]"), /display: none;/);
});

test("an ignored file is greyed behind a dashed edge, so it reads as still there but out of git's sight", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(rule(".file.is-ignored"), /border-style: dashed;/);
  assert.match(rule(".file.is-ignored"), /color: var\(--ink-soft\);/);
  assert.match(rule(".file.is-ignored"), /flex-wrap: wrap;/);
  assert.match(rule(".file.is-ignored .ftag"), /flex: 1 1 100%;/);
});

test("history's chart folds your workshop and dock away, and gives the vault and the mothership the row, growing rather than scrolling", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(css, /\.viz\.is-chart \.viz-row > \.zone\[data-zone="workshop"\],[^{]*\.viz\.is-chart \.zone\[data-zone="dock"\],[^{]*\.viz\.is-chart \.legend \{\s*display: none;/);
  assert.match(rule(".viz.is-chart .viz-row"), /grid-template-columns: minmax\(0, 1fr\) 84px minmax\(0, 1fr\);/);
  assert.match(rule(".viz.is-chart .z-body"), /max-height: none;/);
  assert.match(rule(".cap-gap"), /height: var\(--row, 40px\);/);
  assert.match(rule(".tethers line"), /stroke: var\(--z-re\);/);
  assert.match(rule(".viz-op"), /border: 3px solid var\(--s-mod\);/);
});

test("in history the strip keeps only what folded, except while the vault's card unrolls, and Alex's band runs thin and dashed above", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(css, /\n\.sky\[data-view="history"\]:not\(\.art-birth-unroll\) > \.strip:not\(\.is-band\) \.strip-card:is\(\[data-zone="vault"\], \[data-zone="remote"\]\) \{\s*display: none;/);
  assert.match(rule(".strip.is-band"), /grid-template-columns: auto repeat\(3, minmax\(0, 1fr\)\);/);
  assert.match(rule(".strip.is-band"), /border: 2px dashed/);
  assert.match(rule(".strip.is-band .strip-card"), /padding: 1px 6px;/);
});

test("two sides take the zones' place, and open each conflicted file as a book of two halves in their people's colours", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(rule('.sky[data-view="sides"] .viz'), /display: none;/);
  assert.match(rule(".sides-pages"), /grid-template-columns: minmax\(0, 1fr\) minmax\(0, 1fr\);/);
  assert.match(rule('.sides-half[data-author="alex"]'), /--side: var\(--alex\);/);
  assert.match(rule(".sides-line"), /white-space: pre-wrap;/);
});

test("the kept places are one group only on the black box view, framed there with the workshop outside", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(rule(".viz-kept"), /display: contents;/);
  assert.match(rule(".viz-kept-name"), /display: none;/);
  assert.match(rule('.sky[data-view="blackbox"] .viz-kept'), /display: grid;/);
  assert.match(rule('.sky[data-view="blackbox"] .viz-kept'), /grid-column: 3 \/ -1;/);
  assert.match(rule('.sky[data-view="blackbox"] .viz-kept'), /grid-template-columns: minmax\(0, 1fr\) 42px minmax\(0, 1fr\) 42px minmax\(0, 1fr\);/);
  assert.match(rule('.sky[data-view="blackbox"] .viz-kept-name'), /display: block;/);
});

test("the tape is one scrollable row of ticks, a ghost hollow, the chosen one lit, with the readout under it", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(rule(".tape-track"), /display: flex;/);
  assert.match(rule(".tape-track"), /overflow-x: auto;/);
  assert.match(rule(".tape-tick.is-ghost"), /border-style: dashed;/);
  assert.match(rule(".tape-tick.is-ghost"), /background: transparent;/);
  assert.match(rule('.tape-tick[aria-selected="true"]'), /border-color: var\(--gold\);/);
});

test("a command example wraps its long lines, so no comment hides behind a sideways scroll", () => {
  const block = css.slice(css.indexOf("\npre.code,"), css.indexOf("}", css.indexOf("\npre.code,")));
  assert.match(block, /white-space: pre-wrap;/);
  assert.match(block, /overflow-wrap: anywhere;/);
});

test("dev mode's list sits padded in its panel, its levels without list numbers, since each shows its own", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(rule(".dev"), /padding: 20px 24px;/);
  assert.match(rule(".dev-levels"), /list-style: none;/);
});

test("the field guide over a level is a large dialog that scrolls within itself, over the dimmed level", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(rule(".guide-overlay"), /width: min\(1180px, calc\(100vw - 32px\)\);/);
  assert.match(rule(".guide-overlay"), /max-height: calc\(100vh - 48px\);/);
  assert.match(rule(".guide-overlay"), /overflow-y: auto;/);
  assert.match(rule(".guide-overlay::backdrop"), /background:/);
});

test("Alex wears a green of their own in both looks, and no Alex rule borrows the mothership's pink", () => {
  assert.equal(tokens(css, ":root")["--alex"], "#3D8A18");
  assert.equal(tokens(css, ':root[data-theme="dark"]')["--alex"], "#A6E05A");
  const art = fs.readFileSync(path.join(STATIC, "art-style.css"), "utf8");
  const alexRules = [...`${css}\n${art}`.matchAll(/([^{}]*alex[^{}]*)\{([^}]*)\}/gi)].map((match) => ({ selector: match[1].trim(), body: match[2] }));
  assert.ok(alexRules.length >= 3);
  for (const rule of alexRules) assert.doesNotMatch(rule.body, /--z-re\b/, rule.selector);
  for (const selector of ['.sides-half[data-author="alex"]', '.strip-capsule[data-author="alex"]']) {
    assert.match(alexRules.find((rule) => rule.selector.endsWith(selector)).body, /var\(--alex\)/, selector);
  }
});

test("the chain's lanes stretch to their rows, its walk rests under reduced motion, and a phone drops the hashes, not the names", () => {
  const rule = (selector) => css.slice(css.indexOf(`\n${selector} {`), css.indexOf("}", css.indexOf(`\n${selector} {`)));
  assert.match(rule(".chain-lane"), /height: 100%;/);
  assert.match(rule(".chain-row"), /align-items: stretch;/);
  assert.match(rule(".chain-tag"), /overflow-wrap: anywhere;/);
  assert.match(rule(".chain-subject"), /overflow-wrap: anywhere;/);
  assert.ok(css.slice(css.indexOf("@media (prefers-reduced-motion: reduce)")).includes(".chain-wire.is-walk"));
  const phone = css.slice(css.indexOf("@media (max-width: 600px)"));
  assert.match(phone.slice(0, phone.indexOf("\n}")), /\.chain-hash {\s*display: none;/);
});

test("on a phone the level's head wraps, the buttons with no picture keep their words, and the terminal drops its copy hint", () => {
  const phone = css.slice(css.indexOf("@media (max-width: 600px)"));
  const block = phone.slice(0, phone.indexOf("\n}"));
  assert.match(block, /\.hud {[^}]*flex-wrap: wrap;/);
  assert.match(block, /\.hud \.guide-open \.lbl,\s*\.hud \.solve \.lbl {\s*display: inline;/);
  assert.match(block, /\.termcol \.term-hint {\s*display: none;/);
});

test("on a wide screen a column picture stands right of the mission and the terminal, and keeps in view while the page scrolls", () => {
  const wide = css.slice(css.indexOf("@media (min-width: 1100px)"));
  const block = wide.slice(0, wide.indexOf("\n}"));
  assert.match(block, /\.stage\.is-column {[^}]*grid-template-areas: "mission term viz";/);
  assert.match(block, /\.stage\.is-column \.views {[^}]*position: sticky;/);
});

test("in the column, history's vault and mothership stack with push pointing down and pull up, and no tether crosses", () => {
  const wide = css.slice(css.indexOf("@media (min-width: 1100px)"));
  const block = wide.slice(0, wide.indexOf("\n}"));
  assert.match(block, /\.stage\.is-column \.viz\.is-chart \.viz-row {\s*grid-template-columns: minmax\(0, 1fr\);/);
  assert.match(block, /\.stage\.is-column \.viz\.is-chart \.fl \.art-icon {\s*transform: rotate\(90deg\);/);
  assert.match(block, /\.stage\.is-column \.viz\.is-chart \.fl\.is-back \.art-icon {\s*transform: rotate\(-90deg\);/);
  assert.match(block, /\.stage\.is-column \.viz\.is-chart \.tethers,/);
});
