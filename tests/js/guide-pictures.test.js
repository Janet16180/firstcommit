"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

const document = installBrowser();
const { GuidePictures } = load(["dom.js", "guide-pictures.js"], ["GuidePictures"]);

const words = {
  places: { folder: "Working folder (workshop)", staging: "Staging area (cargo dock)", vault: "Repository (vault)", remote: "Remote (mothership)" },
  notYet: "not there yet",
  empty: "empty",
  head: "HEAD, you are here",
  states: { new: "new", edited: "edited", conflict: "conflict", clean: "saved" },
  ghost: "no name leads here",
  notYours: "on the mothership only",
  by: { you: "your commit", alex: "Alex's commit" },
};
const draw = (model) => {
  const element = GuidePictures.draw(model, words);
  document.body.replaceChildren(element);
  return element;
};
const texts = (element, selector) => [...element.querySelectorAll(selector)].map((node) => node.textContent);

test("a desk draws only the places it names, in Git's order, each labelled with its real name first", () => {
  const desk = draw({ kind: "desk", staging: [], folder: [{ name: "map.txt", state: "new" }] });
  assert.deepEqual(texts(desk, ".gp-place-name"), ["Working folder (workshop)", "Staging area (cargo dock)"]);
});

test("a place that is not there yet says so, and an empty one says it is empty", () => {
  const desk = draw({ kind: "desk", folder: [], staging: null });
  assert.match(desk.querySelector(".gp-place--folder").textContent, /empty/);
  const absent = desk.querySelector(".gp-place--staging");
  assert.ok(absent.classList.contains("gp-place--absent"));
  assert.match(absent.textContent, /not there yet/);
});

test("a file's state is written beside it, so colour is never the only clue, and what just changed is lit", () => {
  const desk = draw({ kind: "desk", folder: [{ name: "map.txt", state: "edited" }], staging: [{ name: "map.txt", fresh: true }] });
  const [inFolder, staged] = desk.querySelectorAll(".gp-chip");
  assert.match(inFolder.textContent, /map\.txt.*edited/);
  assert.ok(inFolder.classList.contains("gp-chip--edited"));
  assert.ok(staged.classList.contains("gp-fresh"));
  assert.ok(!inFolder.classList.contains("gp-fresh"));
});

const chain = (more = {}) => ({
  kind: "chain",
  commits: [{ id: "m", col: 0, parents: ["c", "d"], fresh: true }, { id: "d", col: 1, parents: ["b"], who: "alex" }, { id: "c", col: 0, parents: ["b"] }, { id: "b", col: 0, parents: [] }],
  names: [{ name: "main", on: "m", kind: "branch" }, { name: "scout", on: "d", kind: "branch" }, { name: "origin/main", on: "b", kind: "remote" }],
  head: "main",
  ...more,
});

test("a chain draws one row per commit, newest first, with its names on its row", () => {
  const picture = draw(chain());
  const rows = picture.querySelectorAll(".gp-row");
  assert.equal(rows.length, 4);
  assert.deepEqual(texts(rows[0], ".gp-tag"), ["main"]);
  assert.deepEqual(texts(rows[1], ".gp-tag"), ["scout"]);
  assert.deepEqual(texts(rows[3], ".gp-tag"), ["origin/main"]);
});

test("a merge commit draws a line to each of its parents", () => {
  const picture = draw(chain());
  assert.equal(picture.querySelectorAll(".gp-link").length, 4);
  assert.equal(picture.querySelectorAll(".gp-capsule").length, 4);
});

test("HEAD rides its branch: that tag is filled and marked HEAD; other names keep their kind", () => {
  const picture = draw(chain());
  const main = [...picture.querySelectorAll(".gp-tag")].find((node) => node.textContent === "main");
  assert.ok(main.classList.contains("gp-tag--head"));
  assert.ok(main.parentNode.querySelector(".gp-head"));
  const bookmark = [...picture.querySelectorAll(".gp-tag")].find((node) => node.textContent === "origin/main");
  assert.ok(bookmark.classList.contains("gp-tag--remote"));
  assert.equal(picture.querySelectorAll(".gp-head").length, 1);
});

test("a detached HEAD sits on the commit's own row", () => {
  const picture = draw(chain({ head: "c" }));
  const rows = picture.querySelectorAll(".gp-row");
  assert.ok(rows[2].querySelector(".gp-head"));
  assert.equal(picture.querySelectorAll(".gp-tag--head").length, 0);
});

test("each row tells a screen reader whose commit it is, or that it is a ghost or the mothership's alone", () => {
  const picture = draw({
    kind: "chain",
    commits: [{ id: "c", col: 0, parents: ["b"], who: "mothership" }, { id: "b", col: 0, parents: ["a"], ghost: true }, { id: "a", col: 0, parents: [], who: "alex" }],
    names: [{ name: "main", on: "a", kind: "branch" }],
    head: "main",
  });
  assert.deepEqual(texts(picture, ".gp-row .gp-sr"), ["on the mothership only", "no name leads here", "Alex's commit"]);
  assert.equal(picture.querySelector("svg").getAttribute("aria-hidden"), "true");
});

test("an unknown kind of picture is an error", () => {
  assert.throws(() => GuidePictures.draw({ kind: "tape" }, words), RangeError);
});
