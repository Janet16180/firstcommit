"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const { STATIC } = require("./load");

const css = fs.readFileSync(path.join(STATIC, "fonts.css"), "utf8");
const faces = [...css.matchAll(/@font-face\s*{([^}]*)}/g)].map((match) => match[1]);
const field = (face, name) => (face.match(new RegExp(`${name}:\\s*([^;]+);`)) || [])[1];

test("the three design fonts are declared in the weights the design uses", () => {
  const declared = faces.map((face) => `${field(face, "font-family")} ${field(face, "font-weight")}`).sort();
  assert.deepEqual(declared, ["'Atkinson Hyperlegible' 400", "'Atkinson Hyperlegible' 700", "'Pixelify Sans' 500", "'Pixelify Sans' 700", "'VT323' 400"]);
});

test("every font file ships with the game, served from the page's own static folder", () => {
  const urls = [...css.matchAll(/url\(([^)]+)\)/g)].map((match) => match[1].replace(/["']/g, ""));
  assert.equal(urls.length, faces.length);
  for (const url of urls) {
    assert.match(url, /^\/static\/[\w.-]+\.woff2$/);
    assert.ok(fs.existsSync(path.join(STATIC, url.replace("/static/", ""))), url);
  }
});

test("each font family keeps its OFL licence next to its files", () => {
  for (const name of ["pixelify-sans", "atkinson-hyperlegible", "vt323"]) {
    const licence = fs.readFileSync(path.join(STATIC, `${name}-OFL.txt`), "utf8");
    assert.match(licence, /SIL OPEN FONT LICENSE Version 1\.1/);
  }
});

test("text shows at once in a fallback font while a font loads", () => {
  for (const face of faces) assert.equal(field(face, "font-display"), "swap");
});
