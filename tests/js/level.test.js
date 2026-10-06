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
  const run = page({ active: { ...record("active"), level: ID, step: 3 }, replies: { "/api/check": solved } });
  await settle();
  await settle();
  assert.deepEqual(run.seen.celebrated.map((options) => [options.title, options.xp, options.firstTime]), [["A message that helps", 150, true]]);
  assert.ok(run.q(".debrief"));
  assert.match(run.text(), /Git records what is staged/);
  assert.match(run.text(), /Commands to keep/);
  assert.equal(run.q(".debrief a.next-level"), null);
  assert.ok(run.q(".debrief a[href=\"#/cards/basics\"]"));
});

test("a level solved elsewhere is celebrated from the dashboard's last payout", async () => {
  const payout = { level: ID, xp: 150, first_time: true, rank_before: "Committer", rank_after: "Committer" };
  const refreshed = { ...record("status"), active: null, last_payout: payout };
  const run = page({ active: { ...record("active"), level: ID, step: 1 }, refreshed, replies: { "/api/observe": httpError(409, "no level") } });
  await settle();
  await settle();
  assert.equal(run.seen.celebrated.length, 1);
  assert.ok(run.q(".debrief"));
  assert.match(run.text(), /outside this page/i);
});

test("a level ended elsewhere without a win goes back to its introduction with a note", async () => {
  const refreshed = { ...record("status"), active: null };
  const run = page({ active: { ...record("active"), level: ID, step: 1 }, refreshed, replies: { "/api/observe": httpError(409, "no level") } });
  await settle();
  await settle();
  assert.equal(run.seen.celebrated.length, 0);
  assert.match(run.q(".notice").textContent, /no longer in progress/);
});
