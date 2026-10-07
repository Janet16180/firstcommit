"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

const document = installBrowser();
const { FieldGuide } = load(["dom.js", "art-pixels.js", "art-sprites.js", "art-infographics.js", "infographic-text.js", "field-guide.js"], ["FieldGuide"]);

const level = (id, done) => ({ ...record("status").chapters[1].levels[0], id, title: id, done });
const status = (chapters) => ({ ...record("status"), chapters });
const two = (firstDone, secondDone) => status([{ id: "liftoff", title: "Lift-off", blurb: "", cards: 0, levels: [level("liftoff-aboard", firstDone), level("liftoff-flag", secondDone)] }, { id: "vault", title: "Vault", blurb: "", cards: 0, levels: [] }]);

test("an item unlocks once enough of its chapter's levels are done, in any order", () => {
  assert.equal(FieldGuide.unlocked(two(false, true), { chapter: "liftoff", levels: 1 }), true);
  assert.equal(FieldGuide.unlocked(two(false, true), { chapter: "liftoff", levels: 2 }), false);
  assert.equal(FieldGuide.unlocked(two(true, true), { chapter: "liftoff", levels: 2 }), true);
});

test("a whole chapter unlocks once every one of its levels is done, and a chapter with none yet stays locked", () => {
  assert.equal(FieldGuide.unlocked(two(true, false), { chapter: "liftoff" }), false);
  assert.equal(FieldGuide.unlocked(two(true, true), { chapter: "liftoff" }), true);
  assert.equal(FieldGuide.unlocked(two(true, true), { chapter: "vault" }), false);
  assert.equal(FieldGuide.unlocked(two(true, true), { chapter: "nowhere" }), false);
});

test("the guide shows the four places, a file's states and every command, under a head with the way back to the map", () => {
  const view = FieldGuide.create({ status: () => two(true, false) });
  document.body.replaceChildren(view.element);
  assert.equal(view.element.querySelector("h1").textContent, "Field guide");
  assert.ok(view.element.querySelector('a[href="#/"]'));
  const titles = [...view.element.querySelectorAll(".art-ig-title")].map((node) => node.textContent);
  assert.deepEqual(titles, ["Git's four places", "A file's states", "Every command, by what it does"]);
});

test("what a finished level taught is shown, and the rest is locked", () => {
  const view = FieldGuide.create({ status: () => two(true, false) });
  const text = view.element.textContent;
  assert.match(text, /git status/);
  assert.doesNotMatch(text, /Makes the current folder a repository/);
  assert.match(text, /Not learned yet/);
});

test("a move stays locked while the place or state at either end is", () => {
  const view = FieldGuide.create({ status: () => status([{ id: "cargo", title: "Cargo", blurb: "", cards: 0, levels: [level("one", true), level("two", true)] }]) });
  const states = view.element.querySelector(".art-ig--states").textContent;
  assert.match(states, /git rm --cached/);
  assert.doesNotMatch(states, /git restore --staged/);
});
