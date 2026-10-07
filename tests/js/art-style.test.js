"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { STYLE } = require("./art-check");

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
