"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { installBrowser, load } = require("./load");

installBrowser();
const { ViewTabs, Strings } = load(["dom.js", "strings.js", "view-tabs.js"], ["ViewTabs", "Strings"]);

const names = (row) => [...row.element.querySelectorAll("[role=tab]")].map((tab) => tab.textContent);
const chosen = (row) => [...row.element.querySelectorAll("[role=tab]")].filter((tab) => tab.getAttribute("aria-selected") === "true").map((tab) => tab.dataset.view);

test("the tabs are the views seen, in the ladder's order, the crew view standing in for your station in a crew level", () => {
  assert.deepEqual(ViewTabs.tabs(["history", "station"], false), ["station", "history"]);
  assert.deepEqual(ViewTabs.tabs(["history", "station", "crew"], false), ["station", "history"]);
  assert.deepEqual(ViewTabs.tabs(["station", "crew", "history", "sides"], true), ["crew", "history", "sides"]);
  assert.deepEqual(ViewTabs.tabs(["station", "unknown"], false), ["station"]);
});

test("the row is born with two tabs: one view alone shows no row", () => {
  assert.equal(ViewTabs.create({ tabs: ["station"], current: "station", onPick: () => {} }).element.hidden, true);
  const row = ViewTabs.create({ tabs: ["station", "history"], current: "history", onPick: () => {} });
  assert.equal(row.element.hidden, false);
  assert.deepEqual(names(row), ["Your station", "History"]);
  assert.deepEqual(chosen(row), ["history"]);
});

test("picking a tab says so, and the older view is one tap away", () => {
  const picked = [];
  const row = ViewTabs.create({ tabs: ["station", "history"], current: "history", onPick: (view) => picked.push(view) });
  row.element.querySelector('[data-view="station"]').click();
  assert.deepEqual(picked, ["station"]);
  assert.deepEqual(chosen(row), ["station"]);
});

test("the arrow keys move along the row, as in any tab list", () => {
  const picked = [];
  const row = ViewTabs.create({ tabs: ["station", "history", "sides"], current: "station", onPick: (view) => picked.push(view) });
  const keydown = (key) => row.element.dispatchEvent(Object.assign(makeEvent("keydown"), { key }));
  keydown("ArrowRight");
  keydown("ArrowRight");
  keydown("ArrowRight");
  keydown("ArrowLeft");
  assert.deepEqual(picked, ["history", "sides", "station", "sides"]);
});

test("the tabs speak the page's language", () => {
  Strings.use("es");
  try {
    assert.deepEqual(names(ViewTabs.create({ tabs: ["crew", "history"], current: "crew", onPick: () => {} })), ["Vista de la tripulación", "Historia"]);
  } finally {
    Strings.use("en");
  }
});
