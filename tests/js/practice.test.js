"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { createClock, fakeServer, httpError, installBrowser, load, record, settle } = require("./load");

const document = installBrowser();
const { Practice, createGameApi } = load(
  ["dom.js", "markup.js", "map.js", "api.js", "poll.js", "dialog.js", "live.js", "quest.js", "challenge.js", "practice.js"],
  ["Practice", "createGameApi"],
);

const correct = (step, questDone = false) => ({ correct: true, message: [{ kind: "para", spans: [{ text: "Right.", code: false }] }], step, quest_done: questDone });

/* A practice view on step `step`; `done` is a finished quest (step 3 of 3), which the server lets the page check by itself. */
function practice({ step = 1, done = false, replies = {}, level = record("level") } = {}) {
  const clock = createClock();
  const server = fakeServer({ "/api/observe": record("observation"), "/api/step": record("step"), "/api/check": record("check_unsolved"), "/api/hint": record("hint"), "/api/abort": { level: "x" }, ...replies });
  const seen = { solved: [], ended: 0, left: 0, sounds: [], attached: 0, detached: 0, typed: [] };
  const ctx = {
    game: createGameApi(server.api),
    sound: { play: (name) => seen.sounds.push(name) },
    timers: clock,
    page: document,
    terminal: { attach: () => (seen.attached += 1), detach: () => (seen.detached += 1), type: (text) => seen.typed.push(text) },
  };
  const view = Practice.create(ctx, {
    level,
    active: done ? { ...record("active"), step: 3, auto_check: true } : { ...record("active"), step },
    onSolved: (result) => seen.solved.push(result),
    onEnded: () => (seen.ended += 1),
    onLeft: () => (seen.left += 1),
  });
  document.body.replaceChildren(view.element);
  const routes = () => server.calls.map((call) => call.path);
  return { view, clock, server, seen, routes, q: (selector) => view.element.querySelector(selector) };
}

test("it shows the level, attaches the terminal and draws the lab at once", async () => {
  const run = practice();
  await settle();
  assert.match(run.q(".practice-head").textContent, /A message that helps/);
  assert.equal(run.seen.attached, 1);
  assert.deepEqual(run.routes(), ["/api/observe"]);
  assert.ok(run.q("svg.map-graph"));
  run.view.dispose();
  assert.equal(run.seen.detached, 1);
});

test("an answer step sends the answer, and a wrong one gets the server's nudge", async () => {
  const run = practice();
  await settle();
  run.q(".step.is-current input").value = "README.md";
  run.q(".step.is-current form").dispatchEvent(makeEvent("submit"));
  await settle();
  assert.deepEqual(run.server.calls.at(-1), { path: "/api/step", body: { answer: "README.md" } });
  assert.match(run.q(".step-feedback").textContent, /Not quite/);
  assert.deepEqual(run.seen.sounds, ["wrong"]);
  run.view.dispose();
});

test("a right answer is confirmed, then the next step opens", async () => {
  const run = practice({ replies: { "/api/step": correct(2) } });
  await settle();
  run.q(".step.is-current input").value = "notes.txt";
  run.q(".step.is-current form").dispatchEvent(makeEvent("submit"));
  await settle();
  assert.ok(run.q(".step-feedback").classList.contains("is-correct"));
  await run.clock.advance(Practice.ADVANCE_MS);
  assert.match(run.q(".quest-count").textContent, /Step 3 of 3/);
  run.view.dispose();
});

test("while a watch step is current the page asks about it on every tick, shows its nudge, and moves on once it passes", async () => {
  let passes = false;
  const run = practice({ step: 2, replies: { "/api/step": () => (passes ? correct(3, true) : { ...record("step"), step: 2 }) } });
  await settle();
  const nudge = run.q(".step-feedback p");
  assert.match(run.q(".step-feedback").textContent, /Not quite: look for the line that says modified/);
  assert.ok(run.q(".step-feedback").classList.contains("is-note"));
  await run.clock.advance(1500);
  assert.deepEqual(run.routes(), ["/api/observe", "/api/step", "/api/observe", "/api/step"]);
  assert.equal(run.q(".step-feedback p"), nudge, "the same nudge is not announced again");
  passes = true;
  await run.clock.advance(1500 + Practice.ADVANCE_MS);
  assert.ok(run.q(".challenge"));
  assert.equal(document.activeElement, run.q(".challenge .kicker"));
  assert.deepEqual(run.seen.sounds, ["step"]);
  run.view.dispose();
});

test("once the quest is done the level is checked automatically, and a win stops the polling", async () => {
  const run = practice({ done: true, replies: { "/api/check": record("check_solved") } });
  await settle();
  assert.deepEqual(run.server.calls.map((call) => [call.path, call.body]), [["/api/observe", undefined], ["/api/check", { answer: null, auto: true }]]);
  assert.equal(run.seen.solved.length, 1);
  assert.match(run.q(".check-feedback").textContent, /Solved\./);
  assert.ok(run.q(".check-feedback").classList.contains("is-correct"));
  await run.clock.advance(10000);
  assert.equal(run.server.calls.length, 2);
});

test("a solve reported by two checks at once is handled once", async () => {
  const run = practice({ done: true, replies: { "/api/check": record("check_solved") } });
  run.q(".challenge form").dispatchEvent(makeEvent("submit"));
  await settle();
  assert.equal(run.server.calls.filter((call) => call.path === "/api/check").length, 2);
  assert.equal(run.seen.solved.length, 1);
});

test("once the last step passes, the page checks the level by itself", async () => {
  const run = practice({ step: 2, replies: { "/api/step": correct(3, true), "/api/check": record("check_solved") } });
  await run.clock.advance(Practice.ADVANCE_MS + 1500);
  assert.deepEqual(run.server.calls.find((call) => call.path === "/api/check").body, { answer: null, auto: true });
  assert.equal(run.seen.solved.length, 1);
});

test("an automatic check that does not solve stays silent; it is not a failure of the player's", async () => {
  const run = practice({ done: true });
  await run.clock.advance(3000);
  assert.ok(run.server.calls.filter((call) => call.path === "/api/check").length >= 2);
  assert.equal(run.q(".check-feedback").textContent, "");
  assert.deepEqual(run.seen.sounds, []);
  run.view.dispose();
});

test("checking by hand sends the answer and shows why it is not solved yet", async () => {
  const run = practice({ done: true, level: { ...record("level"), question: [{ kind: "para", spans: [{ text: "Which commit?", code: false }] }], placeholder: "" } });
  await settle();
  run.q(".challenge input").value = "42";
  run.q(".challenge form").dispatchEvent(makeEvent("submit"));
  await settle();
  assert.deepEqual(run.server.calls.at(-1), { path: "/api/check", body: { answer: "42", auto: false } });
  assert.match(run.q(".check-feedback").textContent, /does not hold/);
  run.view.dispose();
});

test("during the quest the player can check the whole level by hand, and hears why it is not solved", async () => {
  const run = practice({ step: 1 });
  await settle();
  run.q(".quest-check button").click();
  await settle();
  assert.deepEqual(run.server.calls.at(-1), { path: "/api/check", body: { answer: null, auto: false } });
  assert.match(run.q(".quest-check .check-feedback").textContent, /does not hold/);
  assert.deepEqual(run.seen.sounds, ["wrong"]);
  run.view.dispose();
});

test("a check by hand during the quest may solve the level early, which stops the polling", async () => {
  const run = practice({ step: 0, replies: { "/api/check": record("check_solved") } });
  await settle();
  run.q(".quest-check button").click();
  await settle();
  assert.equal(run.seen.solved.length, 1);
  assert.match(run.q(".quest-check .check-feedback").textContent, /Solved\./);
  const calls = run.server.calls.length;
  await run.clock.advance(10000);
  assert.equal(run.server.calls.length, calls);
});

test("a hint is revealed in the challenge", async () => {
  const run = practice({ done: true });
  await settle();
  run.q(".hint-button").click();
  await settle();
  assert.match(run.q(".hints").textContent, /git status/);
  run.view.dispose();
});

test("when the level ends elsewhere (409) the polling stops and the owner is told", async () => {
  const run = practice({ replies: { "/api/observe": httpError(409, "no level is in progress") } });
  await settle();
  assert.equal(run.seen.ended, 1);
  await run.clock.advance(10000);
  assert.equal(run.server.calls.length, 1);
});

test("when the server does not answer the page says so and keeps trying", async () => {
  let down = true;
  const run = practice({ replies: { "/api/observe": () => (down ? httpError(0, "no answer") : record("observation")) } });
  await settle();
  assert.equal(run.q(".offline").hidden, false);
  down = false;
  await run.clock.advance(1500);
  assert.equal(run.q(".offline").hidden, true);
  run.view.dispose();
});

test("leaving asks first, then ends the level", async () => {
  const run = practice();
  await settle();
  run.q(".leave").click();
  document.body.querySelector("dialog button.is-confirm").click();
  await settle();
  assert.equal(run.server.calls.at(-1).path, "/api/abort");
  assert.equal(run.seen.left, 1);
});

test("a step's command button types into the terminal", async () => {
  const run = practice();
  await settle();
  run.q(".step.is-current .type-command").click();
  assert.deepEqual(run.seen.typed, ["git status"]);
  run.view.dispose();
});

test("a new commit on the map plays a sound", async () => {
  const observation = record("observation");
  const older = { ...observation, project: { ...observation.project, commits: observation.project.commits.slice(1) } };
  let first = true;
  const run = practice({
    replies: {
      "/api/observe": () => {
        const reply = first ? older : observation;
        first = false;
        return reply;
      },
    },
  });
  await run.clock.advance(1500);
  assert.deepEqual(run.seen.sounds, ["commit"]);
  run.view.dispose();
});
