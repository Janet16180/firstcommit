"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const { Route } = load(["route.js"], ["Route"]);

test("an empty or unknown address is the map", () => {
  for (const hash of ["", "#", "#/", "#/nowhere", "#/level"]) assert.deepEqual(Route.parse(hash), { view: "home" }, hash);
});

test("a level address names the level", () => {
  assert.deepEqual(Route.parse("#/level/cargo-first"), { view: "level", id: "cargo-first" });
  assert.deepEqual(Route.parse("#/level/a%20b"), { view: "level", id: "a b" });
});

test("cards and notes may name a chapter", () => {
  assert.deepEqual(Route.parse("#/cards"), { view: "cards", chapter: null });
  assert.deepEqual(Route.parse("#/cards/basics"), { view: "cards", chapter: "basics" });
  assert.deepEqual(Route.parse("#/notes/hash"), { view: "notes", chapter: "hash" });
});

test("the access key a link may carry after the address is not part of it", () => {
  assert.deepEqual(Route.parse("#/cards&token=abc"), { view: "cards", chapter: null });
  assert.deepEqual(Route.parse("#token=abc"), { view: "home" });
});

test("a broken escape in the address is the map, not an error", () => {
  assert.deepEqual(Route.parse("#/level/%E0%A4%A"), { view: "home" });
});
