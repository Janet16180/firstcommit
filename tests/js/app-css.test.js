"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const { STATIC } = require("./load");

const CSS = fs.readFileSync(path.join(STATIC, "app.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

/* Whether one selector of the form `.feed li[data-kind<op>="value"]` matches an event kind. */
function matches(selector, kind) {
  const found = selector.trim().match(/^\.feed li\[data-kind([\^$*]?)="([^"]+)"\]$/);
  if (!found) return false;
  const [, op, value] = found;
  const tests = { "^": () => kind.startsWith(value), $: () => kind.endsWith(value), "*": () => kind.includes(value), "": () => kind === value };
  return tests[op]();
}

/* The border colour the default look gives a feed event of this kind: the last matching rule's, or null. */
function feedColour(kind) {
  let colour = null;
  for (const [, selectors, body] of CSS.matchAll(/([^{}]+)\{([^}]*)\}/g)) {
    const declared = body.match(/border-left-color:\s*([^;]+);/);
    if (declared && selectors.split(",").some((selector) => matches(selector, kind))) colour = declared[1].trim();
  }
  return colour;
}

test("the default look colours a merge commit like any new commit", () => {
  assert.equal(feedColour("commit-created"), "var(--accent)");
  assert.equal(feedColour("merge-commit-created"), feedColour("commit-created"));
});

test("events with no rule of their own keep the plain border", () => {
  assert.equal(feedColour("file-created"), null);
  assert.equal(feedColour("conflict"), "var(--danger)");
});
