"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const { STATIC, installBrowser, load } = require("./load");

installBrowser();
const { InfographicText, Strings } = load(["strings.js", "infographic-text.js"], ["InfographicText", "Strings"]);

const ROOT = path.join(STATIC, "..", "..", "..", "..");
const chaptersPy = fs.readFileSync(path.join(ROOT, "src", "firstcommit", "chapters.py"), "utf8");
const planned = fs.readFileSync(path.join(ROOT, "docs", "drafts", "chapters-3-7.md"), "utf8").match(/Chapter ids: ([^.]+)\./)[1].match(/`(\w+)`/g).map((id) => id.replaceAll("`", ""));

const items = [
  ...InfographicText.commands.groups.flatMap((group) => group.commands),
  ...InfographicText.places.places,
  ...InfographicText.places.moves,
  ...InfographicText.states.states,
  ...InfographicText.states.moves,
];

test("every item is taught by a chapter that exists or is planned, whole or by a number of its levels", () => {
  for (const item of items) {
    const { chapter, levels, ...rest } = item.taught;
    assert.deepEqual(rest, {}, JSON.stringify(item));
    assert.ok(chaptersPy.includes(`"${chapter}"`) || planned.includes(chapter), JSON.stringify(item));
    assert.ok(levels === undefined || (Number.isInteger(levels) && levels > 0), JSON.stringify(item));
  }
});

test("the places are Git's four, each with its space word and its real Git term", () => {
  assert.deepEqual(InfographicText.places.places.map((place) => [place.space.en, place.git.en]), [["Workshop", "working folder"], ["Cargo dock", "staging area"], ["Vault", "local repository"], ["Mothership", "remote repository"]]);
});

test("the places carry the zone panel's words, in both languages", () => {
  const zones = { workshop: "workshop", dock: "dock", vault: "vault", mothership: "remote" };
  for (const language of ["en", "es"]) {
    Strings.use(language);
    for (const place of InfographicText.places.places) {
      assert.equal(place.space[language], Strings.t(`zones.${zones[place.id]}`), place.id);
      assert.equal(place.git[language], Strings.t(`zones.${zones[place.id]}Git`), place.id);
    }
  }
  Strings.use("en");
});

/* Ids and unlocks are said once; any other word is said in both languages. */
const PLAIN = ["id", "from", "to", "chapter"];
const COMMAND = /^(?:(?:git|ls)\b[\w\-<>".,\s]*|\.gitignore)$/;

function words(value, key, found) {
  if (typeof value === "number") return found;
  if (typeof value === "string") {
    assert.ok(PLAIN.includes(key) || (["command", "how"].includes(key) && COMMAND.test(value)), `${key}: ${value} is in one language only`);
  } else if (Array.isArray(value)) {
    for (const item of value) words(item, key, found);
  } else if ("en" in value) {
    assert.deepEqual(Object.keys(value).sort(), ["en", "es"], JSON.stringify(value));
    assert.ok(value.en.trim() && value.es.trim(), JSON.stringify(value));
    found.push(value);
  } else {
    for (const [name, item] of Object.entries(value)) words(item, name, found);
  }
  return found;
}

test("every word is given in English and in Spanish", () => {
  assert.ok(words(InfographicText, "", []).length > 50);
});

test("the states are a file's four, by their Git names", () => {
  assert.deepEqual(InfographicText.states.states.map((state) => state.name.en), ["untracked", "staged", "committed", "modified"]);
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

/* Engine checked these in git 2.43 (docs/verification/orbit.md, "Field guide text"). */
test("the guide says what git really does, as engine checked it", () => {
  const command = (name) => InfographicText.commands.groups.flatMap((group) => group.commands).find((item) => item.command === name).what.en;
  const place = (id) => InfographicText.places.places.find((item) => item.id === id).what.en;
  const moves = (list, from, to) => list.filter((move) => move.from === from && move.to === to).map((move) => move.command?.en ?? move.how?.en ?? move.command ?? move.how);
  assert.equal(command("git rm --cached <file>"), "Takes a file out of the staging area and keeps it in the working folder. For a file the last commit holds, the next commit then deletes it from the repository.");
  assert.equal(command("git pull"), "A fetch, then brings the remote's commits into your branch: a fast-forward when only the remote moved on; when both did, you choose a merge (--no-rebase) or a rebase (--rebase).");
  assert.deepEqual(moves(InfographicText.places.moves, "mothership", "workshop"), ["git pull (fetch, then merge or rebase)"]);
  assert.equal(place("workshop"), "Your files as you edit them. Git saves nothing here until you add and commit.");
  assert.equal(place("vault"), "Every commit of your repository, yours and the ones you fetched, on this computer, in the hidden .git folder.");
  assert.equal(command("git reset --hard <commit>"), "Moves the current branch's label to another commit, and makes the staging area and the working folder match it: edits not committed are gone. Without --hard, your files stay as they are.");
  assert.deepEqual(moves(InfographicText.states.moves, "staged", "modified"), ["git restore --staged (a file the last commit holds)"]);
  assert.deepEqual(moves(InfographicText.states.moves, "staged", "untracked"), ["git rm --cached (before the file's first commit)", "git restore --staged (a new file, once the repository has a commit)"]);
});

test("switching is taught in Name tags, and clone on the mothership, where the new map teaches them", () => {
  const taughtBy = (command) => items.find((item) => item.command === command).taught.chapter;
  assert.equal(taughtBy("git clone <url>"), "mothership");
  assert.equal(taughtBy("git switch -c <branch>"), "names");
  assert.equal(taughtBy("git switch <branch>"), "names");
  assert.equal(taughtBy("git switch, git restore"), "names");
});

test("the guide lists what Name tags teaches: naming, listing and removing branches, git's tree, and checkout as the older switch", () => {
  const taughtBy = (command) => (items.find((item) => item.command === command) || { taught: {} }).taught.chapter;
  for (const command of ["git branch -v", "git branch <name> <commit>", "git branch -d <name>", "git log --oneline --graph --all", "git checkout <branch>", "git checkout -b <branch>", "git branch <name>"]) assert.equal(taughtBy(command), "names", command);
});
