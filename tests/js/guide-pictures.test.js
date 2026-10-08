"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

const document = installBrowser();
const { GuidePictures, Chain } = load(["dom.js", "strings.js", "places.js", "chain.js", "guide-pictures.js"], ["GuidePictures", "Chain"]);

const words = {
  places: { folder: "Working folder (workshop)", staging: "Staging area (cargo dock)", vault: "Repository (vault)", remote: "Remote (mothership)" },
  notYet: "not there yet",
  empty: "empty",
  head: "HEAD, you are here",
  states: { new: "new", edited: "edited", conflict: "conflict", clean: "saved" },
  ghost: "no name leads here",
  notYours: "on the mothership only",
  by: { you: "your commit", alex: "Alex's commit" },
  marks: { merge: "merge commit", revert: "undoes the one below" },
  gone: "taken off",
  mothership: "mothership",
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
  commits: [{ id: "m", parents: ["c", "d"], fresh: true, mark: "merge" }, { id: "d", parents: ["b"], who: "alex" }, { id: "c", parents: ["b"] }, { id: "b", parents: [] }],
  names: [{ name: "main", on: "m", kind: "branch" }, { name: "scout", on: "d", kind: "branch" }, { name: "origin/main", on: "b", kind: "remote" }],
  head: "main",
  ...more,
});
const row = (picture, id) => picture.querySelector(`.chain-row[data-hash="${id}"]`);

test("a chain is drawn by chain.js's layout and wires, in its look: one row per commit, newest first, with its names", () => {
  const picture = draw(chain());
  assert.ok(picture.classList.contains("chain"));
  assert.deepEqual([...picture.querySelectorAll(".chain-row")].map((node) => node.getAttribute("data-hash")), ["m", "c", "d", "b"], "a side line just above the commit it leaves, as chain.js lays it out");
  assert.equal(picture.querySelectorAll(".chain-cap").length, 4);
  assert.deepEqual(texts(row(picture, "d"), ".chain-tag"), ["scout"]);
  assert.deepEqual(texts(row(picture, "b"), ".chain-tag"), ["origin/main"]);
  assert.equal(picture.style.getPropertyValue("--column-width"), `${Chain.COLUMN}px`);
});

test("HEAD rides its branch: that tag is filled behind the HEAD mark; a bookmark is dashed", () => {
  const picture = draw(chain());
  const main = row(picture, "m").querySelector(".chain-tag");
  assert.ok(main.classList.contains("is-head"));
  const body = [...row(picture, "m").querySelector(".chain-body").children].map((node) => node.className);
  assert.equal(body.indexOf("chain-head") + 1, body.indexOf(main.className));
  assert.ok(row(picture, "b").querySelector(".chain-tag").classList.contains("is-bookmark"));
  assert.equal(picture.querySelectorAll(".chain-head").length, 1);
});

test("a detached HEAD sits on the commit's own row", () => {
  const picture = draw(chain({ head: "c" }));
  assert.ok(row(picture, "c").querySelector(".chain-head"));
  assert.equal(picture.querySelectorAll(".chain-tag.is-head").length, 0);
});

test("what changed is lit: a new commit's ring and its lines to both parents, and a merge commit says what it is", () => {
  const picture = draw(chain());
  assert.ok(row(picture, "m").classList.contains("is-look"));
  assert.ok(row(picture, "m").querySelectorAll(".chain-wire.is-fresh").length >= 2);
  assert.equal(row(picture, "m").querySelector(".gp-mark").textContent, "merge commit");
  assert.ok(!row(picture, "c").classList.contains("is-look"));
});

test("each row tells a screen reader whose commit it is, or that it is a ghost or the mothership's alone", () => {
  const picture = draw({
    kind: "chain",
    commits: [{ id: "c", parents: ["b"], who: "mothership" }, { id: "b", parents: ["a"], ghost: true }, { id: "a", parents: [], who: "alex" }],
    names: [{ name: "main", on: "a", kind: "branch" }],
    head: "main",
  });
  assert.deepEqual(["c", "b", "a"].map((id) => row(picture, id).querySelector(".gp-sr").textContent), ["on the mothership only", "no name leads here", "Alex's commit"]);
  assert.ok(row(picture, "c").classList.contains("is-mothership-only"));
  assert.ok(row(picture, "b").classList.contains("is-ghost"));
  for (const lane of picture.querySelectorAll("svg")) assert.equal(lane.getAttribute("aria-hidden"), "true");
});

test("a name taken off stays drawn, struck through and lit, and says so", () => {
  const picture = draw({ kind: "chain", commits: [{ id: "a", parents: [] }], names: [{ name: "main", on: "a", kind: "branch" }, { name: "test-run", on: "a", kind: "branch", gone: true }], head: "main" });
  const gone = picture.querySelector(".gp-gone .chain-tag");
  assert.equal(gone.textContent, "test-run");
  assert.ok(gone.classList.contains("gp-fresh"));
  assert.match(gone.parentNode.textContent, /taken off/);
});

test("where your bookmark and the mothership agree, one name says both; apart, the mothership is a pin", () => {
  const together = draw({ kind: "chain", commits: [{ id: "a", parents: [] }], names: [{ name: "main", on: "a", kind: "branch" }, { name: "origin/main", on: "a", kind: "remote" }, { name: "mothership", on: "a", kind: "mothership" }], head: "main" });
  assert.deepEqual(texts(together, ".chain-tag"), ["main", "origin/main (mothership)"]);
  assert.equal(together.querySelectorAll(".chain-pin").length, 0);
  const apart = draw({ kind: "chain", commits: [{ id: "b", parents: ["a"], who: "mothership" }, { id: "a", parents: [] }], names: [{ name: "main", on: "a", kind: "branch" }, { name: "origin/main", on: "a", kind: "remote" }, { name: "mothership", on: "b", kind: "mothership" }], head: "main" });
  assert.equal(row(apart, "b").querySelector(".chain-pin.is-mothership").textContent, "mothership");
});

test("an unknown kind of picture is an error", () => {
  assert.throws(() => GuidePictures.draw({ kind: "tape" }, words), RangeError);
});

test("a place that just appeared is lit", () => {
  const desk = draw({ kind: "desk", folder: [], staging: [], fresh: ["staging"] });
  assert.ok(desk.querySelector(".gp-place--staging").classList.contains("gp-fresh"));
  assert.ok(!desk.querySelector(".gp-place--folder").classList.contains("gp-fresh"));
});
