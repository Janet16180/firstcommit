"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { html } = require("./fakedom");
const { installBrowser, load } = require("./load");
const { assertPalette, assertStyled, labelOf, walk } = require("./art-check");

installBrowser();
const { ArtScenes } = load(["dom.js", "art-pixels.js", "art-scenes.js"], ["ArtScenes"]);

test("the scenes are the design's seven the first levels use", () => {
  assert.deepEqual([...ArtScenes.NAMES], ["space", "timeline", "terminal", "planet", "flag", "zones", "conveyor"]);
});

test("every scene is a labelled picture on the 160x90 canvas, in tokens and styled classes only", () => {
  for (const name of ArtScenes.NAMES) {
    const scene = ArtScenes.scene(name);
    assert.equal(scene.getAttribute("viewBox"), "0 0 160 90", name);
    assert.ok(labelOf(scene), `${name} has a description`);
    assertPalette(scene);
    assertStyled(scene);
    assert.equal(html(scene), html(ArtScenes.scene(name)), `${name} is drawn the same each time`);
  }
});

test("a scene takes the page's own label", () => {
  assert.equal(labelOf(ArtScenes.scene("flag", { label: "Planting the flag" })), "Planting the flag");
});

test("the words in the scenes are English and short", () => {
  const words = (name) => [...walk(ArtScenes.scene(name))].filter((node) => node.localName === "text").map((node) => node.textContent);
  assert.deepEqual(words("timeline"), ["v1", "v2", "v3", "v4", "back in time", "every commit is a snapshot"]);
  assert.deepEqual(words("planet"), ["a plain folder", "does Git know it?"]);
  assert.deepEqual(words("zones").filter((word) => ["workshop", "cargo dock", "vault"].includes(word)), ["workshop", "cargo dock", "vault"]);
  assert.ok(words("conveyor").includes("git add picks what goes up"));
  assert.ok(words("flag").includes("git init") && words("flag").includes(".git"));
});

test("the terminal scene lists the folder without naming any file", () => {
  const lines = [...walk(ArtScenes.scene("terminal"))].filter((node) => node.localName === "text").map((node) => node.textContent);
  assert.deepEqual(lines, ["$ ls", "$ git status", "fatal: not a git repository"]);
});

test("an unknown scene is refused", () => {
  assert.throws(() => ArtScenes.scene("moon"), RangeError);
});
