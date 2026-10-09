"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

installBrowser();
const { Sides, Strings } = load(["dom.js", "strings.js", "sides.js"], ["Sides", "Strings"]);

const conflict = () => structuredClone(record("observation").conflicts[0]);
const texts = (node, selector) => [...node.querySelectorAll(selector)].map((item) => item.textContent);

test("a conflicted file opens as a book: your half and Alex's, each named with its branch, its lines in order", () => {
  const sides = Sides.create();
  sides.update([conflict()]);
  const book = sides.element.querySelector(".sides-book");
  assert.equal(book.querySelector(".sides-path").textContent, "docking.txt");
  const halves = [...book.querySelectorAll(".sides-half")];
  assert.deepEqual(halves.map((half) => half.dataset.side), ["you", "them"]);
  assert.deepEqual(halves.map((half) => half.dataset.author), ["you", "alex"]);
  assert.deepEqual(texts(book, ".sides-who"), ["You", "Alex"]);
  assert.deepEqual(texts(book, ".sides-branch"), ["main", "scout"]);
  assert.deepEqual(halves.map((half) => texts(half, ".sides-line")), [["Dock at bay 3"], ["Dock at bay 4"]]);
  assert.deepEqual(texts(book, ".sides-base .sides-line"), ["Dock at bay 2"]);
});

test("a side that deleted the file says so, and a file both sides added has no base", () => {
  const sides = Sides.create();
  sides.update([{ ...conflict(), them: { ...conflict().them, lines: null }, base: null }]);
  assert.equal(sides.element.querySelector('.sides-half[data-side="them"] .sides-deleted').textContent, "Deleted on this side");
  assert.equal(sides.element.querySelector(".sides-base"), null);
});

test("every conflicted file gets its book, and with none the stage says there is no conflict", () => {
  const sides = Sides.create();
  sides.update([conflict(), { ...conflict(), path: "route.txt" }]);
  assert.deepEqual(texts(sides.element, ".sides-path"), ["docking.txt", "route.txt"]);
  sides.update([]);
  assert.equal(sides.element.querySelectorAll(".sides-book").length, 0);
  assert.equal(sides.element.querySelector(".sides-none").textContent, "No file is in conflict.");
});

test("the halves speak the page's language", () => {
  Strings.use("es");
  try {
    const sides = Sides.create();
    sides.update([conflict()]);
    assert.deepEqual(texts(sides.element, ".sides-who"), ["Tú", "Alex"]);
    assert.match(sides.element.querySelector(".sides-base").textContent, /Antes de los dos/);
  } finally {
    Strings.use("en");
  }
});
