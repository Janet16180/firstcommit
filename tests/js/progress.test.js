"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

installBrowser();
const { Progress } = load(["progress.js"], ["Progress"]);

const level = (id, done) => ({ id, title: id, difficulty: 1, xp: 100, done, has_lesson: false, has_quest: false });
const chapters = [
  { id: "one", title: "One", cards: 0, levels: [level("a", true), level("b", false)] },
  { id: "two", title: "Two", cards: 0, levels: [] },
  { id: "three", title: "Three", cards: 0, levels: [level("c", false), level("d", true)] },
];

test("the suggested level is the first one not done", () => {
  assert.equal(Progress.nextLevel(chapters).id, "b");
});

test("after a level, the next one not done comes from later in the map, else from the start", () => {
  assert.equal(Progress.nextLevel(chapters, "b").id, "c");
  assert.equal(Progress.nextLevel(chapters, "c").id, "b");
});

test("the level just played is never suggested again", () => {
  assert.equal(Progress.nextLevel([{ id: "one", title: "One", cards: 0, levels: [level("a", false)] }], "a"), null);
});

test("with everything done there is nothing to suggest", () => {
  const done = chapters.map((chapter) => ({ ...chapter, levels: chapter.levels.map((item) => ({ ...item, done: true })) }));
  assert.equal(Progress.nextLevel(done), null);
});

test("a level is found by id with its chapter", () => {
  assert.deepEqual(Progress.findLevel(chapters, "c").chapter.id, "three");
  assert.equal(Progress.findLevel(chapters, "zzz"), null);
});

test("the rank bar shows how far the XP is between this rank and the next", () => {
  assert.deepEqual(Progress.rankProgress(record("status")), { fraction: 0.2, toNext: 240 });
  const top = { ...record("status"), rank: { title: "Maintainer", floor: 5000, next_title: null, next_at: null } };
  assert.deepEqual(Progress.rankProgress(top), { fraction: 1, toNext: null });
});
