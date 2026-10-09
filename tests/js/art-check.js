"use strict";

/*
 * Checks the art-* tests share: the colour tokens a picture may use (the design's :root tokens
 * and art-style.css's --art-* ones), the classes art-style.css and art-infographics.css define, and
 * walks over a picture.
 */

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { STATIC } = require("./load");

const DESIGN = fs.readFileSync(path.join(__dirname, "..", "..", "docs", "drafts", "orbit-design.html"), "utf8");
const STYLE = fs.readFileSync(path.join(STATIC, "art-style.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

const declared = (css) => [...css.matchAll(/(--[\w-]+)\s*:/g)].map((match) => match[1]);
const designRoot = DESIGN.slice(DESIGN.indexOf(":root{"), DESIGN.indexOf("*,*::before"));
const TOKENS = new Set([...declared(designRoot), ...declared(STYLE.slice(0, STYLE.indexOf("}")))]);
const INFOGRAPHICS_STYLE = fs.readFileSync(path.join(STATIC, "art-infographics.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const STYLE_CLASSES = new Set([...(STYLE + INFOGRAPHICS_STYLE).matchAll(/\.(art-[\w-]+)/g)].map((match) => match[1]));

function* walk(node) {
  yield node;
  for (const child of node.children) yield* walk(child);
}

/* Every colour the picture paints with: fills, strokes and var() colours in style attributes. */
function colours(node) {
  const found = [];
  for (const element of walk(node)) {
    for (const name of ["fill", "stroke"]) if (element.hasAttribute(name)) found.push(element.getAttribute(name));
    const style = element.getAttribute("style") || "";
    for (const match of style.matchAll(/(?:background|fill|stroke|color)\s*:\s*([^;]+)/g)) found.push(match[1].trim());
  }
  return found;
}

/* The picture paints only with design tokens (or currentColor, or nothing). */
function assertPalette(node) {
  const painted = colours(node);
  assert.ok(painted.length > 0, "the picture paints something");
  for (const colour of painted) {
    if (colour === "none" || colour === "currentColor") continue;
    const token = colour.match(/^var\((--[\w-]+)\)$/);
    assert.ok(token, `${colour} is a token`);
    assert.ok(TOKENS.has(token[1]), `${token[1]} is a design or art token`);
  }
}

/* Every art-* class the picture uses is styled in art-style.css or art-infographics.css; modifiers (art-icon--lock) are
   hooks for the page and need no rule of their own. */
function assertStyled(node) {
  for (const element of walk(node)) {
    for (const name of element.classList.list().filter((word) => word.startsWith("art-") && !word.includes("--"))) assert.ok(STYLE_CLASSES.has(name), `${name} is in art-style.css`);
  }
}

const isHidden = (node) => node.getAttribute("aria-hidden") === "true" && !node.hasAttribute("aria-label");
const labelOf = (node) => (node.getAttribute("role") === "img" ? node.getAttribute("aria-label") : null);

module.exports = { STYLE, INFOGRAPHICS_STYLE, TOKENS, walk, colours, assertPalette, assertStyled, isHidden, labelOf };
