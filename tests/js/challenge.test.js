"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { installBrowser, load, record } = require("./load");

installBrowser();
const { Challenge } = load(["dom.js", "markup.js", "challenge.js"], ["Challenge"]);

function challenge(active = { ...record("active"), step: 3, hints: 0 }) {
  const seen = { checks: [], hints: 0 };
  const made = Challenge.create({ level: record("level"), active, onCheck: (answer) => seen.checks.push(answer), onHint: () => (seen.hints += 1) });
  return { ...made, seen, q: (selector) => made.element.querySelector(selector) };
}

test("the challenge shows the briefing", () => {
  const view = challenge();
  assert.match(view.q(".briefing").textContent, /record the change to notes\.txt/);
});

test("checking sends the typed answer, or null when the box is empty", () => {
  const view = challenge();
  view.q("form").dispatchEvent(makeEvent("submit"));
  view.q("input").value = "  abc123 ";
  view.q("form").dispatchEvent(makeEvent("submit"));
  assert.deepEqual(view.seen.checks, [null, "abc123"]);
});

test("a hint is asked for on its button and shown with its cost", () => {
  const view = challenge();
  assert.match(view.q(".hint-button").textContent, /3 left/);
  view.q(".hint-button").click();
  assert.equal(view.seen.hints, 1);
  view.addHint(record("hint"));
  assert.match(view.q(".hints").textContent, /Look at what git status lists/);
  assert.match(view.q(".hints").textContent, /10 XP/);
  assert.match(view.q(".hint-button").textContent, /2 left/);
});

test("with every hint used the button is off, and hints used earlier are counted", () => {
  const view = challenge({ ...record("active"), step: 3, hints: 3, hints_total: 3 });
  assert.equal(view.q(".hint-button").disabled, true);
  assert.match(view.q(".hints-used").textContent, /3 of 3/);
});

test("the result of a check is shown", () => {
  const view = challenge();
  view.feedback(record("check_unsolved").message, false);
  assert.match(view.q(".check-feedback").textContent, /does not hold the new notes\.txt/);
  assert.ok(view.q(".check-feedback").classList.contains("is-wrong"));
});
