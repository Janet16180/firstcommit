"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

const document = installBrowser();
const { Collection } = load(["dom.js", "markup.js", "progress.js", "collection.js"], ["Collection"]);

const texts = (nodes) => [...nodes].map((node) => node.textContent);

test("the collection opens as a dialog with a card for every mission, in play order", () => {
  const status = record("status");
  const dialog = Collection.open(status);
  assert.ok(dialog.open);
  assert.equal(dialog.querySelector("h2").textContent, "Command collection");
  assert.equal(dialog.querySelectorAll(".cmdcard").length, 2);
  dialog.close();
});

test("a finished mission's card shows its command and what it does, in its sector's colour", () => {
  const dialog = Collection.open(record("status"));
  const card = dialog.querySelector(".cmdcard");
  assert.equal(card.querySelector("code").textContent, "git init");
  assert.equal(card.querySelector("p").textContent, "Makes the current folder a repository.");
  assert.equal(card.dataset.sector, "1");
  dialog.close();
});

test("a mission not finished yet keeps its card locked", () => {
  const dialog = Collection.open(record("status"));
  const locked = dialog.querySelectorAll(".cmdcard.is-locked");
  assert.equal(locked.length, 1);
  assert.deepEqual(texts(locked[0].querySelectorAll("p")), ["Finish mission 2.2 to unlock it."]);
  dialog.close();
});

test("closing the dialog removes it from the page", () => {
  const dialog = Collection.open(record("status"));
  dialog.querySelector("button.close").click();
  assert.equal(document.body.querySelector("dialog.collection"), null);
});
