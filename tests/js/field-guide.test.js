"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

const document = installBrowser();
const { FieldGuide, Strings } = load(["dom.js", "strings.js", "art-pixels.js", "art-sprites.js", "art-infographics.js", "infographic-text.js", "field-guide.js"], ["FieldGuide", "Strings"]);

const level = (id, done) => ({ ...record("status").chapters[1].levels[0], id, title: id, done });
const status = (chapters) => ({ ...record("status"), chapters });
const two = (firstDone, secondDone) => status([{ id: "liftoff", title: "Lift-off", blurb: "", cards: 0, levels: [level("liftoff-aboard", firstDone), level("liftoff-flag", secondDone)] }, { id: "vault", title: "Vault", blurb: "", cards: 0, levels: [] }]);

test("an item is taught once enough of its chapter's levels are done, in any order", () => {
  assert.equal(FieldGuide.taught(two(false, true), { chapter: "liftoff", levels: 1 }), true);
  assert.equal(FieldGuide.taught(two(false, true), { chapter: "liftoff", levels: 2 }), false);
  assert.equal(FieldGuide.taught(two(true, true), { chapter: "liftoff", levels: 2 }), true);
});

test("a whole chapter is taught once every one of its levels is done; a chapter with none yet has taught nothing", () => {
  assert.equal(FieldGuide.taught(two(true, false), { chapter: "liftoff" }), false);
  assert.equal(FieldGuide.taught(two(true, true), { chapter: "liftoff" }), true);
  assert.equal(FieldGuide.taught(two(true, true), { chapter: "vault" }), false);
  assert.equal(FieldGuide.taught(two(true, true), { chapter: "nowhere" }), false);
});

test("the guide shows the four places, a file's states and every command, under a head with the way back to the map", () => {
  const view = FieldGuide.create({ status: () => two(true, false) });
  document.body.replaceChildren(view.element);
  assert.equal(view.element.querySelector("h1").textContent, "Field guide");
  assert.ok(view.element.querySelector('a[href="#/"]'));
  const titles = [...view.element.querySelectorAll(".art-ig-title")].map((node) => node.textContent);
  assert.deepEqual(titles, ["Git's four places", "A file's states", "Every command, by what it does"]);
});

test("everything is readable from the start, nothing locked", () => {
  const view = FieldGuide.create({ status: () => two(false, false) });
  const text = view.element.textContent;
  assert.match(text, /git status/);
  assert.match(text, /Makes the current folder a repository/);
  assert.match(text, /a file the last commit holds/);
  assert.doesNotMatch(text, /Not learned yet/);
  assert.equal(view.element.querySelector(".art-ig-lock"), null);
});

test("what a sector still ahead teaches is tagged with that sector; what is taught carries no tag", () => {
  const view = FieldGuide.create({ status: () => two(true, false) });
  const tags = [...view.element.querySelectorAll(".art-ig-tag")].map((node) => node.textContent);
  assert.ok(tags.includes("Coming up in sector 1"));
  assert.ok(tags.includes("Coming up in sector 2"));
  const card = [...view.element.querySelectorAll(".art-ig-card")].find((node) => /git status/.test(node.textContent));
  assert.equal(card.querySelector(".art-ig-tag"), null);
});

test("a sector the map does not list yet is coming up later", () => {
  const view = FieldGuide.create({ status: () => two(true, true) });
  const tags = [...view.element.querySelectorAll(".art-ig-tag")].map((node) => node.textContent);
  assert.ok(tags.includes("Coming up later"));
});

test("a move is tagged by what teaches it alone, whatever its ends", () => {
  const view = FieldGuide.create({ status: () => status([{ id: "cargo", title: "Cargo", blurb: "", cards: 0, levels: [level("one", true), level("two", true)] }]) });
  const states = view.element.querySelector(".art-ig--states");
  assert.match(states.textContent, /a file the last commit holds/);
  const tagged = [...states.querySelectorAll(".art-ig-move")].filter((node) => node.classList.contains("art-ig-move--upcoming")).length;
  assert.ok(tagged < states.querySelectorAll(".art-ig-move").length);
});

test("opened over a level, the guide's head offers to close it instead of the way to the map", () => {
  let closed = 0;
  const view = FieldGuide.create({ status: () => two(true, false) }, { onClose: () => (closed += 1) });
  assert.equal(view.element.querySelector('a[href="#/"]'), null);
  view.element.querySelector(".guide-close").click();
  assert.equal(closed, 1);
});

test("the guide speaks the page's language", () => {
  Strings.use("es");
  try {
    const view = FieldGuide.create({ status: () => two(true, false) });
    assert.equal(view.element.querySelector("h1").textContent, "Guía de campo");
    assert.match(view.element.querySelector('a[href="#/"]').textContent, /Mapa/);
    assert.match(view.element.textContent, /Taller/);
    assert.match(view.element.textContent, /Llega en el sector 2/);
    assert.doesNotMatch(view.element.textContent, /Workshop/);
  } finally {
    Strings.use("en");
  }
});
