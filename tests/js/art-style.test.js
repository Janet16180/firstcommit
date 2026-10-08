"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { STYLE, TOKENS } = require("./art-check");

const rules = (selector) => [...STYLE.matchAll(/([^{}]+)\{([^{}]*)\}/g)].filter(([, selectors]) => selectors.split(",").some((part) => part.trim() === selector)).map(([, , body]) => body);

test("every animation runs on a keyframes rule the sheet defines, in steps", () => {
  const keyframes = new Set([...STYLE.matchAll(/@keyframes\s+([\w-]+)/g)].map((match) => match[1]));
  const used = [...STYLE.matchAll(/animation:\s*([\w-]+)\s+([^;]+);/g)].filter(([, name]) => name !== "none");
  assert.ok(used.length > 10);
  for (const [, name, rest] of used) {
    assert.ok(keyframes.has(name), `${name} is defined`);
    assert.match(rest, /steps\(\d+\)/, `${name} runs in steps`);
  }
});

test("reduced motion stops the art's animations and hides the burst", () => {
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.ok(reduced.length > 0 && reduced.includes("@media"));
  assert.match(reduced, /\.art-scene \*[\s\S]*animation: none !important/);
  assert.match(reduced, /\.art-sparks\s*\{\s*display: none;/);
});

test("the art tokens are fixed colours, the same in light and dark mode", () => {
  assert.equal(STYLE.match(/--art-[\w-]+:\s*#[0-9A-F]{6};/g).length, STYLE.match(/--art-[\w-]+:/g).length);
  assert.ok(!STYLE.includes("prefers-color-scheme"));
  assert.equal(rules(":root").length, 1);
});

test("a conflicted file chip shakes once while a crack flashes over it", () => {
  assert.match(rules(".art-crack").join(""), /animation: art-crack 0\.6s steps\(\d+\)/);
  const crack = rules(".art-crack::after").join("");
  assert.match(crack, /content: ""/);
  assert.match(crack, /position: absolute/);
  assert.match(crack, /animation: art-crack-flash 0\.6s steps\(\d+\)/);
  assert.match(rules(".art-crack").join(""), /position: relative/);
});

test("a revert capsule rises from below upside down and turns upright", () => {
  assert.match(rules(".art-rise-inverted").join(""), /animation: art-rise-inverted 0\.8s steps\(\d+\) both/);
  const frames = STYLE.slice(STYLE.indexOf("@keyframes art-rise-inverted"));
  assert.match(frames, /from \{ transform: translateY\(\d+px\) scaleY\(-1\)/);
});

test("the conflict and paused merge icons wear their state colours unless the page sets one", () => {
  assert.match(rules(".art-icon--conflict").join(""), /color: var\(--s-new\)/);
  assert.match(rules(".art-icon--merging").join(""), /color: var\(--s-mod\)/);
  assert.match(rules(".art-icon--inverted").join(""), /color: var\(--zc, var\(--z-va\)\)/);
});

test("reduced motion stops the crack, the inverted rise and the blinking pause bar", () => {
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  for (const selector of [".art-crack", ".art-crack::after", ".art-rise-inverted", ".art-pause"]) assert.ok(reduced.includes(selector), selector);
});

test("a station frames its zones in its crew member's colour, with a name tab on the border", () => {
  const frame = rules(".art-station").join("");
  assert.match(frame, /--station-colour: var\(--z-va\)/);
  assert.match(frame, /border: 4px solid var\(--station-colour\)/);
  assert.match(frame, /min-width: 0/);
  assert.match(rules(".art-station--you").join(""), /--station-colour: var\(--z-va\)/);
  assert.match(rules(".art-station--alex").join(""), /--station-colour: var\(--z-re\)/);
  const tab = rules(".art-station-name").join("");
  assert.match(tab, /position: absolute/);
  assert.match(tab, /border: 3px solid var\(--station-colour\)/);
  assert.match(tab, /background: var\(--panel\)/);
});

test("a flying capsule trails an exhaust flame, above it when it lands", () => {
  const flame = rules(".art-crew-flight::after").join("");
  assert.match(flame, /content: ""/);
  assert.match(flame, /top: 100%/);
  assert.match(flame, /animation: art-crew-flame 0\.2s steps\(2\) infinite/);
  assert.match(rules(".art-crew-flight--down::after").join(""), /bottom: 100%/);
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.ok(reduced.includes(".art-crew-flight::after"));
});

const BIRTH = "var(--art-birth, 1.4s)";
const frames = (name) => STYLE.slice(STYLE.indexOf(`@keyframes ${name}`)).match(/^@keyframes[^{]*\{([\s\S]*?\}\s*)\}/)[1];
const birthAnimation = (selector) => rules(selector).join("").match(/animation: ([\w-]+) (.+?) steps\(\d+\) both;/);

test("the fold folds each zone up toward the strip, small and faded, over the page's birth time", () => {
  const zone = rules(".sky.art-birth-fold .viz .zone").join("");
  assert.match(zone, /transform-origin: top/);
  const [, name, duration] = birthAnimation(".sky.art-birth-fold .viz .zone");
  assert.equal(duration, BIRTH);
  assert.match(frames(name), /to \{ transform: translateY\(-\d+px\) scale\(0\.\d+, 0\.\d+\); opacity: 0; \}/);
});

test("in the fold each strip card lands from below, where its zone was, and stays", () => {
  assert.match(rules(".sky.art-birth-fold .strip-card").join(""), /transform-origin: bottom/);
  const [, name, duration] = birthAnimation(".sky.art-birth-fold .strip-card");
  assert.equal(duration, BIRTH);
  assert.match(frames(name), /from \{ transform: translateY\(\d+px\) scale\(0\.\d+\); opacity: 0; \}/);
  assert.match(frames(name), /to \{ transform: none; opacity: 1; \}/);
});

test("in the fold the flows and the legend fade out", () => {
  const [, flow, duration] = birthAnimation(".sky.art-birth-fold .viz .flow");
  assert.equal(duration, BIRTH);
  assert.deepEqual(birthAnimation(".sky.art-birth-fold .viz .legend").slice(1), [flow, BIRTH]);
  assert.match(frames(flow), /to \{ opacity: 0; \}/);
});

test("the unroll reveals every vault from the top down, then the mothership fades in", () => {
  const [, unroll, duration] = birthAnimation('.sky.art-birth-unroll .viz .zone[data-zone$="vault"]');
  assert.equal(duration, BIRTH);
  assert.match(frames(unroll), /from \{ clip-path: inset\(0 0 100% 0\); \}/);
  assert.match(frames(unroll), /clip-path: inset\(0\);/);
  const [, mothership, after] = birthAnimation('.sky.art-birth-unroll .viz .zone[data-zone="remote"]');
  assert.equal(after, BIRTH);
  assert.match(frames(mothership), /0%, \d+% \{ opacity: 0; \}/);
  assert.match(frames(mothership), /to \{ opacity: 1; \}/);
});

test("the unroll starts with the strip's vault card lit in its own colour", () => {
  const [, name, duration] = birthAnimation('.sky.art-birth-unroll .strip-card[data-zone="vault"]');
  assert.equal(duration, BIRTH);
  assert.match(frames(name), /background: color-mix\(in srgb, var\(--zc\) \d+%, var\(--panel\)\)/);
});

test("the births paint only with the design's tokens", () => {
  const births = STYLE.slice(STYLE.indexOf(".sky.art-birth-fold"), STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.ok(births.length > 0);
  for (const [, name] of births.matchAll(/var\((--[\w-]+)/g)) assert.ok(TOKENS.has(name) || ["--art-birth", "--zc"].includes(name), name);
  assert.ok(!/#[0-9A-Fa-f]{3,6}\b|\brgba?\(|\bhsla?\(/.test(births));
});

test("reduced motion plays neither birth", () => {
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  for (const selector of [".sky.art-birth-fold *", ".sky.art-birth-unroll *"]) assert.ok(reduced.includes(selector), selector);
});

test("an ignored folder's chip sits behind a calm scanline field with emitters at its corners, behind its words", () => {
  const chip = rules(".art-ignore-field").join("");
  assert.match(chip, /position: relative/);
  assert.match(chip, /isolation: isolate/);
  const field = rules(".art-ignore-field::after").join("");
  assert.match(field, /content: ""/);
  assert.match(field, /position: absolute/);
  assert.match(field, /z-index: -1/);
  assert.match(field, /pointer-events: none/);
  assert.match(field, /repeating-linear-gradient\(/);
  assert.equal((field.match(/no-repeat/g) || []).length, 4, "four corner emitters");
  for (const [, token] of field.matchAll(/var\((--[\w-]+)/g)) assert.ok(TOKENS.has(token), token);
  assert.ok(!/#[0-9A-Fa-f]{3,6}\b|\brgba?\(|\bhsla?\(/.test(field));
  assert.ok(!/::before/.test(STYLE.match(/\.art-ignore-field[^{]*\{/g).join("")), "the chip's ::before is its state dot");
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.ok(reduced.includes(".art-ignore-field::after"));
});
