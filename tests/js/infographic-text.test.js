"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const { STATIC, installBrowser, load } = require("./load");

installBrowser();
const { InfographicText } = load(["infographic-text.js"], ["InfographicText"]);

const ROOT = path.join(STATIC, "..", "..", "..", "..");
const levelIds = fs.readdirSync(path.join(ROOT, "src", "firstcommit", "levels")).filter((name) => name.endsWith(".py") && name !== "__init__.py").map((name) => name.replace(".py", "").replaceAll("_", "-"));
const chaptersPy = fs.readFileSync(path.join(ROOT, "src", "firstcommit", "chapters.py"), "utf8");
const planned = fs.readFileSync(path.join(ROOT, "docs", "drafts", "chapters-3-7.md"), "utf8").match(/Chapter ids: ([^.]+)\./)[1].match(/`(\w+)`/g).map((id) => id.replaceAll("`", ""));

const items = [
  ...InfographicText.commands.groups.flatMap((group) => group.commands),
  ...InfographicText.places.places,
  ...InfographicText.places.moves,
  ...InfographicText.states.states,
  ...InfographicText.states.moves,
];

test("every item says what unlocks it: a level that exists, or a chapter that exists or is planned", () => {
  for (const item of items) {
    const { level, chapter } = item.unlock;
    assert.ok(level ? levelIds.includes(level) : chaptersPy.includes(`"${chapter}"`) || planned.includes(chapter), JSON.stringify(item));
  }
});

test("the places are Git's four, each with its space word and its real Git term", () => {
  assert.deepEqual(InfographicText.places.places.map((place) => [place.space, place.git]), [["Workshop", "working folder"], ["Cargo dock", "staging area"], ["Vault", "local repository"], ["Mothership", "remote repository"]]);
});

test("the states are a file's four, by their Git names", () => {
  assert.deepEqual(InfographicText.states.states.map((state) => state.name), ["untracked", "staged", "committed", "modified"]);
});

test("every move joins two places or two states that exist", () => {
  const places = InfographicText.places.places.map((place) => place.id);
  const states = InfographicText.states.states.map((state) => state.id);
  for (const move of InfographicText.places.moves) assert.ok(places.includes(move.from) && places.includes(move.to), move.command);
  for (const move of InfographicText.states.moves) assert.ok(states.includes(move.from) && states.includes(move.to), move.how);
});

test("each command is listed once", () => {
  const commands = InfographicText.commands.groups.flatMap((group) => group.commands.map((item) => item.command));
  assert.equal(new Set(commands).size, commands.length);
});

test("the text is frozen data", () => {
  assert.ok(Object.isFrozen(InfographicText));
});
