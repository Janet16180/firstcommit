"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const { STATIC } = require("./load");

const CSS = fs.readFileSync(path.join(STATIC, "theme-time-share.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const NARROW = CSS.indexOf("@container ts-share");

/* The share grid's grid-template-areas in a piece of the stylesheet, as rows of area names. */
function template(css) {
  const found = css.match(/\.ts-grid\s*\{[^}]*grid-template-areas:\s*((?:"[^"]*"\s*)+);/);
  return found[1].match(/"[^"]*"/g).map((row) => row.slice(1, -1).trim().split(/\s+/));
}

const LAYOUTS = { wide: template(CSS.slice(0, NARROW)), narrow: template(CSS.slice(NARROW)) };

/* Each named area's rectangle in a template: {top, bottom, left, right}, inclusive. */
function rectangles(rows) {
  const found = {};
  rows.forEach((row, y) => row.forEach((name, x) => {
    const was = found[name] || { top: y, bottom: y, left: x, right: x };
    found[name] = { top: Math.min(was.top, y), bottom: Math.max(was.bottom, y), left: Math.min(was.left, x), right: Math.max(was.right, x) };
  }));
  return found;
}

/* The heading drawn over a place: the person's name, or GitHub's. */
const heading = (place) => `${place.split("-")[0]}-who`;

/* What lies in a template's rows strictly between `from` and `to`, over some columns. */
const between = (rows, from, to, left, right) => rows.slice(from + 1, to).flatMap((row) => row.slice(left, right + 1));

/* Whether an upright arrow in `gap` joins `from` and `to`: it is above one and below the other,
   shares columns with both, and only the dots of empty cells or the places' own headings lie
   between it and each place. */
function joins(rows, from, gap, to) {
  const area = rectangles(rows);
  const [a, g, b] = [area[from], area[gap], area[to]];
  const overlaps = (one, other) => one.left <= other.right && other.left <= one.right;
  const above = (one, other) => one.bottom < other.top;
  const allowed = new Set([".", heading(from), heading(to)]);
  const gapTo = (place) => (above(place, g) ? between(rows, place.bottom, g.top, g.left, g.right) : between(rows, g.bottom, place.top, g.left, g.right));
  const clear = (place) => gapTo(place).every((name) => allowed.has(name));
  const ordered = (above(a, g) && above(g, b)) || (above(b, g) && above(g, a));
  return Boolean(a && g && b) && ordered && overlaps(a, g) && overlaps(g, b) && clear(a) && clear(b);
}

const JOINS = ["you", "alex"].flatMap((who) => [
  [`${who}-folder`, `${who}-gap-1`, `${who}-index`],
  [`${who}-index`, `${who}-gap-2`, `${who}-repository`],
  [`${who}-repository`, `${who}-gap-3`, "github-remote"],
]);

test("in both layouts every arrow stands between the two places it moves work between", () => {
  for (const [layout, rows] of Object.entries(LAYOUTS)) {
    for (const [from, gap, to] of JOINS) assert.ok(joins(rows, from, gap, to), `${layout}: ${gap} joins ${from} and ${to}`);
  }
});

test("wide, you and Alex stand side by side, and GitHub spans the whole width below both", () => {
  const area = rectangles(LAYOUTS.wide);
  const width = LAYOUTS.wide[0].length;
  assert.ok(area["you-repository"].right < area["alex-repository"].left, "you on the left, Alex on the right");
  assert.equal(area["you-folder"].top, area["alex-folder"].top, "both computers start on the same row");
  assert.deepEqual([area["github-remote"].left, area["github-remote"].right], [0, width - 1]);
  assert.ok(area["github-remote"].top > Math.max(area["you-gap-3"].bottom, area["alex-gap-3"].bottom), "GitHub is below both");
});

test("narrow, one column: you, then GitHub, then Alex's computer upside down, its repository nearest GitHub", () => {
  assert.ok(LAYOUTS.narrow.every((row) => row.length === 1));
  const order = LAYOUTS.narrow.map(([name]) => name);
  const at = (name) => order.indexOf(name);
  assert.ok(at("you-folder") < at("you-repository") && at("you-repository") < at("github-remote"));
  assert.ok(at("github-remote") < at("alex-repository") && at("alex-repository") < at("alex-index") && at("alex-index") < at("alex-folder"));
});

test("each person's slot for buttons is under the figure, and the switch is above the slots on a narrow screen", () => {
  const wide = rectangles(LAYOUTS.wide);
  for (const who of ["you", "alex"]) {
    assert.ok(wide[`${who}-slot`].top > wide["github-remote"].bottom, `${who}'s slot is under GitHub`);
    assert.ok(wide[`${who}-slot`].left === wide[`${who}-folder`].left, `${who}'s slot is in ${who}'s column`);
  }
  const order = LAYOUTS.narrow.map(([name]) => name);
  assert.deepEqual(order.slice(-3), ["switch", "you-slot", "alex-slot"]);
});

test("every area a part of the figure is placed in exists in the layouts that show it", () => {
  const placed = [...CSS.matchAll(/grid-area:\s*([a-z0-9-]+)\s*;/g)].map((found) => found[1]);
  for (const name of new Set(placed)) {
    assert.ok(LAYOUTS.narrow.flat().includes(name), `narrow has ${name}`);
    if (name !== "switch") assert.ok(LAYOUTS.wide.flat().includes(name), `wide has ${name}`);
  }
  for (const name of new Set([...LAYOUTS.wide.flat(), ...LAYOUTS.narrow.flat()])) {
    if (name !== ".") assert.ok(placed.includes(name), `something is placed in ${name}`);
  }
});
