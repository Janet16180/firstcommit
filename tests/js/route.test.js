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
  assert.deepEqual(Route.parse("#/cards/cargo"), { view: "cards", chapter: "cargo" });
  assert.deepEqual(Route.parse("#/notes/vault"), { view: "notes", chapter: "vault" });
});

test("the access key a link may carry after the address is not part of it", () => {
  assert.deepEqual(Route.parse("#/cards&token=abc"), { view: "cards", chapter: null });
  assert.deepEqual(Route.parse("#token=abc"), { view: "home" });
});

test("a broken escape in the address is the map, not an error", () => {
  assert.deepEqual(Route.parse("#/level/%E0%A4%A"), { view: "home" });
});

test("the field guide has its own address", () => {
  assert.deepEqual(Route.parse("#/guide"), { view: "guide" });
});

test("dev mode's level list has its own address", () => {
  assert.deepEqual(Route.parse("#/dev"), { view: "dev" });
  assert.deepEqual(Route.parse("#/dev/anything"), { view: "dev" });
});

test("the playground's address may name a start, a view and a line to try", () => {
  assert.deepEqual(Route.parse("#/playground"), { view: "playground", start: null, picture: null, tryLine: null });
  assert.deepEqual(Route.parse("#/playground?start=branches&view=chain&try=git%20switch%20-c%20test"), { view: "playground", start: "branches", picture: "chain", tryLine: "git switch -c test" });
  assert.deepEqual(Route.parse("#/playground?try=git%20log%20--oneline%20%26%26%20ls"), { view: "playground", start: null, picture: null, tryLine: "git log --oneline && ls" });
});

test("the access key after a playground address is left out of it, and a broken escape names nothing", () => {
  assert.deepEqual(Route.parse("#/playground?start=lost&token=abc"), { view: "playground", start: "lost", picture: null, tryLine: null });
  assert.deepEqual(Route.parse("#/playground?start=%E0%A4%A&view=desk"), { view: "playground", start: null, picture: "desk", tryLine: null });
});

test("an address without its access key keeps everything else", () => {
  assert.equal(Route.address("#/playground?start=lost&try=ls&token=abc"), "#/playground?start=lost&try=ls");
  assert.equal(Route.address("#/cards&token=abc"), "#/cards");
  assert.equal(Route.address("#token=abc"), "#");
});
