"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { createClock, fakeServer, httpError, installBrowser, load, record, settle } = require("./load");

const document = installBrowser({ reducedMotion: true });
const { LevelScreen, createGameApi } = load(
  ["dom.js", "markup.js", "art-pixels.js", "art-sprites.js", "art-sky.js", "api.js", "progress.js", "poll.js", "zones.js", "zone-panel.js", "mission.js", "comms.js", "completion.js", "level-screen.js"],
  ["LevelScreen", "createGameApi"],
);

const para = (text) => [{ kind: "para", spans: [{ text, code: false }] }];
const correct = (step, questDone = false) => ({ correct: true, message: para("Right."), step, quest_done: questDone });

/* A level screen for the sample level; `active` is the level in progress as the status first says (null: none). */
function screen({ active = record("active"), replies = {}, levelId = "sample-second" } = {}) {
  const clock = createClock();
  let status = { ...record("status"), active };
  const server = fakeServer({
    "/api/level": record("level"),
    "/api/start": { ...record("active"), step: 0 },
    "/api/observe": record("observation"),
    "/api/step": record("step"),
    "/api/check": record("check_unsolved"),
    "/api/hint": record("hint"),
    ...replies,
  });
  const seen = { sounds: [], attached: 0, detached: 0, typed: [], reloads: 0, refreshed: 0 };
  const ctx = {
    game: createGameApi(server.api),
    status: () => status,
    refresh: async () => {
      seen.refreshed += 1;
      if (server.calls.some((call) => call.path === "/api/start")) status = { ...status, active: record("active") };
      return status;
    },
    reload: () => (seen.reloads += 1),
    sound: { play: (name) => seen.sounds.push(name) },
    timers: clock,
    page: document,
    reducedMotion: true,
    terminal: {
      attach: (host) => {
        seen.attached += 1;
        seen.host = host;
      },
      detach: () => (seen.detached += 1), type: (text) => seen.typed.push(text) },
    setStatus: (next) => (status = next),
  };
  const view = LevelScreen.create(ctx, levelId);
  document.body.replaceChildren(view.element);
  const routes = () => server.calls.map((call) => call.path.split("?")[0]);
  return { view, ctx, clock, server, seen, routes, q: (selector) => view.element.querySelector(selector), all: (selector) => [...view.element.querySelectorAll(selector)] };
}

test("a mission in progress opens at once: its number and title in the head, the zones, the goals, Rama and the terminal", async () => {
  const run = screen();
  await settle();
  assert.equal(run.q(".hud-num").textContent, "Mission 2.2");
  assert.equal(run.q(".hud-name").textContent, "A message that helps");
  assert.ok(run.q(".viz .zone"));
  assert.equal(run.all(".goal").length, 3);
  assert.ok(run.q(".comms"));
  assert.equal(run.seen.attached, 1);
  assert.ok(run.seen.host.classList.contains("termcol"));
  assert.deepEqual(run.routes(), ["/api/level", "/api/observe"]);
  run.view.dispose();
  assert.equal(run.seen.detached, 1);
});

test("the head leads back to the map and offers a restart, with drawn icons, never typed ones", async () => {
  const run = screen();
  await settle();
  const back = run.q(".hud a.btn");
  assert.equal(back.getAttribute("href"), "#/");
  assert.ok(back.querySelector("svg.art-icon"));
  assert.match(run.q(".hud .restart").textContent, /Restart/);
  assert.doesNotMatch(run.q(".hud").textContent, /[←-⇿☀-➿]/);
  run.view.dispose();
});

test("a mission not in progress is started first, then shown", async () => {
  const run = screen({ active: null });
  assert.match(run.q(".comms").textContent, /Preparing/);
  await settle();
  await settle();
  assert.deepEqual(run.routes().slice(0, 3), ["/api/start", "/api/level", "/api/observe"]);
  assert.deepEqual(run.server.calls[0].body, { level: "sample-second" });
  assert.equal(run.seen.attached, 1);
  run.view.dispose();
});

test("an unknown mission says there is none, with a way back to the map", async () => {
  const run = screen({ active: null, levelId: "nowhere", replies: { "/api/start": httpError(404) } });
  await settle();
  assert.match(run.view.element.textContent, /There is no mission here/);
  assert.ok(run.q('a[href="#/"]'));
  assert.equal(run.seen.attached, 0);
});

test("the zones are drawn from every observation", async () => {
  const run = screen();
  await settle();
  assert.equal(run.q('.zone[data-zone="vault"] .chash').textContent, "547cd2b");
  run.view.dispose();
});

test("a wrong answer gets the server's nudge on Rama's line", async () => {
  const run = screen();
  await settle();
  const form = run.q(".goal.is-current form");
  form.querySelector("input").value = "README.md";
  form.dispatchEvent(makeEvent("submit"));
  await settle();
  assert.deepEqual(run.server.calls.at(-1).body, { answer: "README.md" });
  assert.match(run.q(".comms").textContent, /Not quite/);
  assert.equal(run.q(".comms").dataset.mood, "err");
  assert.deepEqual(run.seen.sounds, ["wrong"]);
  run.view.dispose();
});

test("a right answer is confirmed and the next goal becomes current", async () => {
  const run = screen({ replies: { "/api/step": correct(2) } });
  await settle();
  const form = run.q(".goal.is-current form");
  form.querySelector("input").value = "notes.txt";
  form.dispatchEvent(makeEvent("submit"));
  await settle();
  assert.equal(run.q(".comms").dataset.mood, "ok");
  assert.ok(run.all(".goal")[2].classList.contains("is-current"));
  run.view.dispose();
});

test("a goal to read moves on with Continue", async () => {
  const run = screen({ active: { ...record("active"), step: 0 }, replies: { "/api/step": correct(1) } });
  await settle();
  run.q(".goal-continue").click();
  await settle();
  assert.deepEqual(run.server.calls.at(-1).body, { answer: null });
  assert.ok(run.all(".goal")[1].classList.contains("is-current"));
  run.view.dispose();
});

test("while a watch goal is current, every tick asks about it, and it passes by itself", async () => {
  let passed = false;
  const run = screen({ active: { ...record("active"), step: 2 }, replies: { "/api/step": () => (passed ? correct(3, true) : { ...record("step"), step: 2 }) } });
  await settle();
  assert.deepEqual(run.routes(), ["/api/level", "/api/observe", "/api/step"]);
  assert.equal(run.q(".comms").dataset.mood, "info");
  passed = true;
  await run.clock.advance(1500);
  assert.equal(run.all(".goal.is-done").length, 3);
  run.view.dispose();
});

test("once the quest is done the mission is checked by itself; a solve stops the polling and docks the lesson at the bottom", async () => {
  const run = screen({ active: { ...record("active"), step: 3, auto_check: true }, replies: { "/api/check": record("check_solved") } });
  await settle();
  await settle();
  const dock = run.q(".dock");
  assert.ok(dock);
  assert.equal(dock.querySelector(".dock-title").textContent, "Mission complete: mission 2.2");
  assert.match(dock.querySelector(".dock-lesson").textContent, /Git records what is staged/);
  assert.ok(run.view.element.classList.contains("is-docked"));
  assert.ok(run.seen.sounds.includes("celebrate"));
  const calls = run.server.calls.length;
  await run.clock.advance(10000);
  assert.equal(run.server.calls.length, calls);
  assert.equal(run.seen.detached, 0);
  run.view.dispose();
});

test("an automatic check that does not solve stays silent", async () => {
  const run = screen({ active: { ...record("active"), step: 3, auto_check: true } });
  await settle();
  assert.match(run.q(".comms").textContent, /Read the goals/);
  assert.deepEqual(run.seen.sounds, []);
  run.view.dispose();
});

test("the dock's Retry starts the mission again and shows it afresh", async () => {
  const run = screen({ active: { ...record("active"), step: 3, auto_check: true }, replies: { "/api/check": record("check_solved") } });
  await settle();
  await settle();
  run.q(".dock .btn").click();
  await settle();
  assert.equal(run.routes().at(-1), "/api/start");
  assert.equal(run.seen.reloads, 1);
  run.view.dispose();
});

test("Restart in the head starts the mission again", async () => {
  const run = screen();
  await settle();
  run.q(".hud .restart").click();
  await settle();
  assert.equal(run.routes().at(-1), "/api/start");
  assert.equal(run.seen.reloads, 1);
  run.view.dispose();
});

test("a hint is revealed in the panel and Rama points at it", async () => {
  const run = screen();
  await settle();
  run.q(".hint-row button").click();
  await settle();
  assert.equal(run.all(".hint-list div").length, 1);
  assert.match(run.q(".comms").textContent, /hint/);
  assert.deepEqual(run.seen.sounds, ["hint"]);
  run.view.dispose();
});

test("a command clicked in the panel is typed in the terminal", async () => {
  const run = screen();
  await settle();
  run.all(".goal")[1].querySelector("pre code").click();
  assert.deepEqual(run.seen.typed, ["git status"]);
  run.view.dispose();
});

test("a mission solved from the command line shows the dock with its lesson", async () => {
  const run = screen({ replies: { "/api/observe": httpError(409) } });
  run.ctx.setStatus({ ...record("status"), active: null, last_payout: { ...record("status").last_payout, level: "sample-second" } });
  await settle();
  await settle();
  assert.ok(run.q(".dock"));
  run.view.dispose();
});

test("a mission ended elsewhere without a solve says so on Rama's line and stops", async () => {
  const run = screen({ replies: { "/api/observe": httpError(409) } });
  await settle();
  await settle();
  assert.match(run.q(".comms").textContent, /no longer in progress/);
  assert.equal(run.q(".dock"), null);
  const calls = run.server.calls.length;
  await run.clock.advance(10000);
  assert.equal(run.server.calls.length, calls);
  run.view.dispose();
});

test("when the server does not answer Rama says so, and the page keeps trying", async () => {
  let down = true;
  const run = screen({ replies: { "/api/observe": () => (down ? httpError(0) : record("observation")) } });
  await settle();
  assert.match(run.q(".comms").textContent, /not answering/);
  down = false;
  await run.clock.advance(1500);
  assert.doesNotMatch(run.q(".comms").textContent, /not answering/);
  run.view.dispose();
});
