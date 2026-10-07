"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { html } = require("./fakedom");
const { installBrowser, load } = require("./load");
const { assertPalette, assertStyled, labelOf, walk } = require("./art-check");

installBrowser();
const { ArtScenes } = load(["dom.js", "art-pixels.js", "art-scenes.js"], ["ArtScenes"]);

test("the scenes are the design's thirteen and the four new ones of chapters 5 to 7", () => {
  assert.deepEqual([...ArtScenes.NAMES], [
    "space", "timeline", "terminal", "planet", "flag", "zones", "conveyor",
    "capsule", "chain", "orbit", "rocket", "pull", "alarm",
    "fork", "merge", "collision", "blackbox",
  ]);
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

const wordsOf = (name) => [...walk(ArtScenes.scene(name))].filter((node) => node.localName === "text").map((node) => node.textContent);

test("the chapter 3 to 7 scenes say little, in English", () => {
  assert.deepEqual(wordsOf("capsule"), ["vault", "a1b2c3d", '-m "first liftoff"', "git commit"]);
  assert.deepEqual(wordsOf("chain").slice(0, 6), ["a1b2c3d", "liftoff", "f00d42e", "Phobos stop", "9c0ffee", "logbook"]);
  assert.ok(wordsOf("chain").includes("HEAD"));
  assert.deepEqual(wordsOf("orbit"), ["your base (local)", "origin"]);
  assert.deepEqual(wordsOf("rocket"), ["git remote add", "git push"]);
  assert.deepEqual(wordsOf("pull"), ["Alex's commit", "git pull"]);
  assert.deepEqual(wordsOf("alarm"), ["base 7", "alert"]);
  assert.deepEqual(wordsOf("fork"), ["feature", "main", "git switch -c feature"]);
  assert.deepEqual(wordsOf("merge"), ["main", "git merge"]);
  assert.deepEqual(wordsOf("collision"), ["CONFLICT", "same file, same lines"]);
  assert.deepEqual(wordsOf("blackbox"), ["main", "reflog"]);
});

test("the moving pictures move with the art sheet's step animations", () => {
  const classes = (name) => [...walk(ArtScenes.scene(name))].flatMap((node) => node.classList.list());
  const moves = { capsule: ["art-drop", "art-lid"], orbit: ["art-orbit"], rocket: ["art-push"], pull: ["art-pull"], alarm: ["art-meteor", "art-boom", "art-alarm"], fork: ["art-slide"], collision: ["art-slide"], blackbox: ["art-vanish", "art-slide"], merge: ["art-pop"] };
  for (const [name, wanted] of Object.entries(moves)) for (const className of wanted) assert.ok(classes(name).includes(className), `${name} uses ${className}`);
});

test("the terminal scene lists the folder without naming any file", () => {
  const lines = [...walk(ArtScenes.scene("terminal"))].filter((node) => node.localName === "text").map((node) => node.textContent);
  assert.deepEqual(lines, ["$ ls", "$ git status", "fatal: not a git repository"]);
});

test("an unknown scene is refused", () => {
  assert.throws(() => ArtScenes.scene("moon"), RangeError);
});
