"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { createClock, fakeServer, httpError, installBrowser, load, record, settle } = require("./load");

const document = installBrowser();
const { LevelPage, createGameApi } = load(
  ["dom.js", "markup.js", "map.js", "api.js", "progress.js", "poll.js", "dialog.js", "live.js", "quest.js", "challenge.js", "lesson.js", "practice.js", "level.js"],
  ["LevelPage", "createGameApi"],
);

const ID = "sample-second";

function page({ active = null, replies = {}, refreshed = null } = {}) {
  const status = { ...record("status"), active };
  const server = fakeServer({
    "/api/level": record("level"),
    "/api/lesson": record("lesson"),
    "/api/start": { ...record("active"), step: 0 },
    "/api/observe": record("observation"),
    "/api/step": record("step"),
    "/api/check": record("check_unsolved"),
    ...replies,
  });
  const seen = { celebrated: [], refreshed: 0 };
  const ctx = {
    game: createGameApi(server.api),
    status: () => status,
    refresh: async () => {
      seen.refreshed += 1;
      return refreshed || status;
    },
    celebrate: async (options) => seen.celebrated.push(options),
    sound: { play() {} },
    timers: createClock(),
    page: document,
    reducedMotion: true,
    terminal: { attach() {}, detach() {}, type() {} },
  };
  const view = LevelPage.create(ctx, ID);
  document.body.replaceChildren(view.element);
  return { view, server, seen, ctx, q: (selector) => view.element.querySelector(selector), text: () => view.element.textContent };
}

const button = (run, label) => run.view.element.querySelectorAll("button").find((item) => label.test(item.textContent));

test("an unknown level says so and links back to the map", async () => {
  const run = page({ replies: { "/api/level": httpError(404, "unknown id") } });
  await settle();
  assert.match(run.text(), /no level/i);
  assert.ok(run.q("a[href=\"#/\"]"));
});

test("a level not in progress introduces itself with its facts and what comes first", async () => {
  const run = page();
  await settle();
  assert.match(run.q("h1").textContent, /A message that helps/);
  assert.match(run.text(), /150 XP/);
  assert.match(run.text(), /lesson, then a guided quest/i);
  assert.ok(button(run, /Start the lesson/));
  assert.ok(button(run, /Skip to the practice/));
});

test("another level in progress is named, since starting this one ends it", async () => {
  const run = page({ active: { ...record("active"), level: "sample-first" } });
  await settle();
  assert.match(run.q(".notice").textContent, /Your first commit.*in progress/);
});

test("starting builds the lab, refreshes the dashboard and opens the practice", async () => {
  const run = page();
  await settle();
  button(run, /Skip to the practice/).click();
  await settle();
  assert.deepEqual(run.server.calls.find((call) => call.path === "/api/start").body, { level: ID });
  assert.equal(run.seen.refreshed, 1);
  assert.ok(run.q(".practice"));
  assert.match(run.q(".quest-count").textContent, /Step 1 of 3/);
  run.view.dispose();
});

test("after starting, the level is read again so its text is filled from the new lab", async () => {
  let started = false;
  const level = () => {
    const view = record("level");
    view.steps[0].text = [{ kind: "para", spans: [{ text: started ? "You are on trunk." : "You are on {{branch}}.", code: false }] }];
    return view;
  };
  const start = () => {
    started = true;
    return { ...record("active"), step: 0 };
  };
  const run = page({ replies: { "/api/level": level, "/api/start": start } });
  await settle();
  button(run, /Skip to the practice/).click();
  await settle();
  assert.match(run.q(".step.is-current").textContent, /You are on trunk\./);
  run.view.dispose();
});

test("a level already in progress opens straight into the practice", async () => {
  const run = page({ active: { ...record("active"), level: ID, step: 1 } });
  await settle();
  assert.ok(run.q(".practice"));
  assert.match(run.q(".quest-count").textContent, /Step 2 of 3/);
  run.view.dispose();
});

test("the lesson plays, and finishing it starts the level", async () => {
  const run = page();
  await settle();
  button(run, /Start the lesson/).click();
  await settle();
  assert.ok(run.q(".lesson"));
  for (let slide = 0; slide < 5; slide += 1) run.q(".lesson-next").click();
  await settle();
  assert.ok(run.q(".practice"));
  run.view.dispose();
});

test("a win is celebrated, then the debrief teaches and suggests what comes next", async () => {
  const solved = record("check_solved");
  const run = page({ active: { ...record("active"), level: ID, step: 3, auto_check: true }, replies: { "/api/check": solved } });
  await settle();
  await settle();
  assert.deepEqual(run.seen.celebrated.map((options) => [options.title, options.xp, options.firstTime]), [["A message that helps", 150, true]]);
  assert.ok(run.q(".debrief"));
  assert.match(run.text(), /Git records what is staged/);
  assert.match(run.text(), /Commands to keep/);
  assert.equal(run.q(".debrief a.next-level"), null);
  assert.ok(run.q(".debrief a[href=\"#/cards/basics\"]"));
});

test("the debrief of a replay shows the XP the server paid and says it was played again", async () => {
  const solved = record("check_solved");
  const replay = { ...solved, payout: { ...solved.payout, xp: 40, first_time: false } };
  const run = page({ active: { ...record("active"), level: ID, step: 3, auto_check: true }, replies: { "/api/check": replay } });
  await settle();
  await settle();
  assert.deepEqual(run.seen.celebrated.map((options) => [options.xp, options.firstTime]), [[40, false]]);
  assert.match(run.q(".payout").textContent, /Played again/);
  assert.match(run.q(".payout").textContent, /\+40 XP/);
});

test("a level solved elsewhere is celebrated from the dashboard's last payout, then shows its debrief", async () => {
  const payout = { level: ID, xp: 150, first_time: true, rank_before: "Committer", rank_after: "Committer" };
  const refreshed = { ...record("status"), active: null, last_payout: payout };
  let finished = false;
  const level = () => ({ ...record("level"), debrief: finished ? record("check_solved").debrief : null });
  const observe = () => {
    finished = true;
    return httpError(409, "no level");
  };
  const run = page({ active: { ...record("active"), level: ID, step: 1 }, refreshed, replies: { "/api/level": level, "/api/observe": observe } });
  await settle();
  await settle();
  await settle();
  assert.equal(run.seen.celebrated.length, 1);
  assert.ok(run.q(".debrief"));
  assert.match(run.text(), /Git records what is staged/);
});

test("a finished level offers its debrief again from its introduction, without a payout", async () => {
  const run = page({ replies: { "/api/level": { ...record("level"), debrief: record("check_solved").debrief } } });
  await settle();
  button(run, /Read the debrief/).click();
  assert.match(run.text(), /Commands to keep/);
  assert.equal(run.q(".payout"), null);
});

test("a level ended elsewhere without a win goes back to its introduction with a note", async () => {
  const refreshed = { ...record("status"), active: null };
  const run = page({ active: { ...record("active"), level: ID, step: 1 }, refreshed, replies: { "/api/observe": httpError(409, "no level") } });
  await settle();
  await settle();
  assert.equal(run.seen.celebrated.length, 0);
  assert.match(run.q(".notice").textContent, /no longer in progress/);
});
