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
