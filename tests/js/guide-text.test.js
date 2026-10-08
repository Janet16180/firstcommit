"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const { STATIC, installBrowser, load } = require("./load");

installBrowser();
const { GuideText, InfographicText, GuideGit } = load(["infographic-text.js", "guide-git.js", "guide-text.js"], ["GuideText", "InfographicText", "GuideGit"]);

const ROOT = path.join(STATIC, "..", "..", "..", "..");
const LEVELS = path.join(ROOT, "src", "firstcommit", "levels");
/* Each level's chapter, command label (COMMAND, the label the map's records carry) and whether it
   is a challenge, read from its file. */
const levels = fs.readdirSync(LEVELS).filter((name) => /^[a-z]+_[a-z0-9]+\.py$/.test(name)).map((name) => {
  const text = fs.readFileSync(path.join(LEVELS, name), "utf8");
  return { chapter: name.split("_")[0], command: text.match(/^COMMAND = "([^"]*)"/m)[1], challenge: /^CHALLENGE = True/m.test(text) };
});
const listed = InfographicText.commands.groups.flatMap((group) => group.commands);

test("every command of the guide has a card, and every card is a command of the guide", () => {
  assert.deepEqual(GuideText.cards.map((card) => card.command).sort(), listed.map((item) => item.command).sort());
});

test("a card's lessons are command labels of missions, one of them in the chapter that tags the command", () => {
  for (const card of GuideText.cards) {
    const { taught } = listed.find((item) => item.command === card.command);
    assert.ok(card.lessons.length > 0, card.command);
    for (const lesson of card.lessons) assert.ok(levels.some((level) => level.command === lesson), `${card.command}: ${lesson}`);
    assert.ok(levels.some((level) => level.chapter === taught.chapter && card.lessons.includes(level.command)), card.command);
  }
});

test("every mission that teaches is some card's lesson, so nothing taught is missing from the guide", () => {
  const lessons = new Set(GuideText.cards.flatMap((card) => card.lessons));
  for (const level of levels.filter((item) => !item.challenge)) assert.ok(lessons.has(level.command), `${level.chapter}: ${level.command}`);
});

test("a card's output is a transcript real git printed", () => {
  for (const card of GuideText.cards) {
    assert.ok(card.runs.length > 0, card.command);
    for (const run of card.runs) assert.ok(GuideGit.runs[run], `${card.command}: ${run}`);
  }
});

test("related commands are other cards", () => {
  const commands = GuideText.cards.map((card) => card.command);
  for (const card of GuideText.cards) {
    assert.ok(card.related.length > 0, card.command);
    for (const other of card.related) assert.ok(commands.includes(other) && other !== card.command, `${card.command}: ${other}`);
  }
});

const PLACES = ["folder", "staging", "vault", "remote"];
const CHIP_STATES = ["new", "edited", "conflict", "clean", "ignored", undefined];
const NAME_KINDS = ["branch", "remote", "mothership"];

function checkDesk(desk, where) {
  const keys = Object.keys(desk).filter((key) => key !== "kind" && key !== "fresh");
  for (const key of desk.fresh || []) assert.ok(keys.includes(key), where);
  assert.ok(keys.length > 0 && keys.every((key) => PLACES.includes(key)), where);
  for (const key of keys) {
    if (desk[key] === null) continue;
    for (const chip of desk[key]) {
      assert.equal(typeof chip.name, "string", where);
      assert.ok(CHIP_STATES.includes(chip.state), where);
    }
  }
}

function checkChain(chain, where) {
  const ids = chain.commits.map((commit) => commit.id);
  assert.equal(new Set(ids).size, ids.length, where);
  chain.commits.forEach((commit, index) => {
    for (const parent of commit.parents) assert.ok(ids.indexOf(parent) > index, `${where}: ${commit.id} is newer than its parent ${parent}`);
  });
  for (const name of chain.names) {
    assert.ok(ids.includes(name.on), `${where}: ${name.name}`);
    assert.ok(NAME_KINDS.includes(name.kind), `${where}: ${name.kind}`);
  }
  const branches = chain.names.filter((name) => name.kind === "branch").map((name) => name.name);
  assert.ok(branches.includes(chain.head) || ids.includes(chain.head), `${where}: HEAD on ${chain.head}`);
}

test("every picture is a desk or a chain whose parts exist, and the after picture is the same kind", () => {
  for (const card of GuideText.cards) {
    const { before, after } = card.picture;
    for (const [side, picture] of [["before", before], ["after", after]]) {
      if (!picture) continue;
      const where = `${card.command} ${side}`;
      assert.ok(["desk", "chain"].includes(picture.kind), where);
      if (picture.kind === "desk") checkDesk(picture, where);
      else checkChain(picture, where);
    }
    assert.ok(!after || after.kind === before.kind, card.command);
  }
});

function words(value, found) {
  if (typeof value !== "object" || value === null) return found;
  if (Array.isArray(value)) {
    for (const item of value) words(item, found);
  } else if ("en" in value) {
    assert.deepEqual(Object.keys(value).sort(), ["en", "es"], JSON.stringify(value));
    assert.ok(value.en.trim() && value.es.trim(), JSON.stringify(value));
    found.push(value);
  } else {
    for (const item of Object.values(value)) words(item, found);
  }
  return found;
}

const lit = (picture) => (picture.kind === "desk"
  ? (picture.fresh || []).length > 0 || ["folder", "staging", "vault", "remote"].some((key) => (picture[key] || []).some((chip) => chip.fresh))
  : picture.commits.some((commit) => commit.fresh) || picture.names.some((name) => name.fresh || name.gone));

test("every after picture lights what the command changed", () => {
  for (const card of GuideText.cards.filter((item) => item.picture.after)) assert.ok(lit(card.picture.after), card.command);
});

/* The free playground's starts and views (records.py's StartId and PlaygroundView on
   p2/orbit-engine, docs/drafts/playground/plan.md). */
const STARTS = ["empty", "changes", "branches", "alex-ahead", "both", "conflict", "lost"];
const VIEWS = ["chain", "history", "desk", "crew", "conflict", "movelog", "graph"];

function checkPlayground(link, where) {
  assert.ok(STARTS.includes(link.start), `${where}: start ${link.start}`);
  assert.ok(link.view === undefined || VIEWS.includes(link.view), `${where}: view ${link.view}`);
  assert.deepEqual(Object.keys(link).filter((key) => !["start", "view", "try"].includes(key)), [], where);
  if (link.try === undefined) return;
  assert.match(link.try, /^(?:git|ls) [^\n]+$/, `${where}: try ${link.try}`);
  assert.ok(!/[<>]/.test(link.try), `${where}: a try is a real command, not a placeholder: ${link.try}`);
}

test("every card links to a playground start that suits it, with a real one-line command to try", () => {
  for (const card of GuideText.cards) checkPlayground(card.playground, card.command);
  const tries = GuideText.cards.filter((card) => card.playground.try).length;
  assert.ok(tries >= GuideText.cards.length - 3, `${tries} cards have a try`);
});

test("the conflict walkthrough links to the conflict start, in its conflict view", () => {
  assert.deepEqual(GuideText.conflict.playground, { start: "conflict", view: "conflict" });
});

test("every word is given in English and in Spanish, and each card has its mistake in both", () => {
  assert.ok(words(GuideText, []).length > 60);
  for (const card of GuideText.cards) assert.ok(card.mistake.en && card.mistake.es, card.command);
});

test("the conflict's words name the real markers git wrote", () => {
  assert.match(GuideGit.conflict.markers, /^<<<<<<< HEAD$/m);
  assert.match(GuideGit.conflict.markers, /^>>>>>>> alex-route$/m);
  assert.equal(GuideText.conflict.steps.length, 7);
});

test("the text is frozen data", () => {
  assert.ok(Object.isFrozen(GuideText));
});
