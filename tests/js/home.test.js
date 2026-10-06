"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { fakeServer, installBrowser, load, record, settle } = require("./load");

const document = installBrowser();
const { HomeView, createGameApi } = load(["dom.js", "api.js", "progress.js", "dialog.js", "home.js"], ["HomeView", "createGameApi"]);

function home(status = record("status")) {
  const server = fakeServer({ "/api/reset": {} });
  const seen = { refreshed: 0, shown: 0 };
  const ctx = { game: createGameApi(server.api), status: () => status, refresh: async () => (seen.refreshed += 1), reload: () => (seen.shown += 1) };
  const view = HomeView.create(ctx);
  document.body.replaceChildren(view.element);
  return { view, server, seen, q: (selector) => view.element.querySelector(selector), all: (selector) => view.element.querySelectorAll(selector) };
}

test("the rank shows the XP and how far the next rank is", () => {
  const run = home();
  assert.equal(run.q(".hero h1").textContent, "Committer");
  assert.match(run.q(".hero").textContent, /260 XP · 240 XP to Brancher/);
  assert.equal(run.q(".meter").getAttribute("aria-valuenow"), "20");
});

test("a level in progress is offered first, with how far its quest is", () => {
  const run = home();
  const link = run.q(".hero a.btn-primary");
  assert.equal(link.getAttribute("href"), "#/level/sample-second");
  assert.match(link.textContent, /Continue: A message that helps/);
  assert.match(run.q(".hero").textContent, /step 2 of 3/);
});

test("with no level in progress the next level not done is suggested", () => {
  const run = home({ ...record("status"), active: null });
  assert.match(run.q(".hero a.btn-primary").textContent, /Next: A message that helps/);
});

test("cards due are offered beside it", () => {
  const run = home();
  assert.match(run.q(".hero a[href=\"#/cards\"]").textContent, /Review 4 cards/);
});

test("chapters are listed in order with their levels, done levels marked and empty chapters waiting", () => {
  const run = home();
  const chapters = run.all(".chapter");
  assert.deepEqual(chapters.map((chapter) => chapter.querySelector("h2").textContent), ["Git, GitHub and your first clone", "The three areas", "Fingerprints"]);
  assert.match(chapters[0].textContent, /Coming soon/);
  const levels = chapters[1].querySelectorAll("a.level-link");
  assert.deepEqual(levels.map((link) => link.getAttribute("href")), ["#/level/sample-first", "#/level/sample-second"]);
  assert.ok(levels[0].classList.contains("is-done"));
  assert.ok(levels[1].classList.contains("is-active"));
  assert.ok(chapters[1].querySelector("a[href=\"#/notes/basics\"]"));
  assert.match(chapters[1].querySelector("a[href=\"#/cards/basics\"]").textContent, /12 cards/);
});

test("a level's difficulty is shown on the scale the server sends", () => {
  const run = home({ ...record("status"), max_difficulty: 5 });
  const meta = run.all(".chapter")[1].querySelectorAll(".level-meta").map((item) => item.textContent);
  assert.deepEqual(meta, ["●○○○○ · 100 XP", "●●○○○ · 150 XP"]);
});

test("erasing all progress asks first, then resets and shows the fresh map", async () => {
  const run = home();
  run.q(".erase").click();
  document.body.querySelector("dialog button.is-confirm").click();
  await settle();
  assert.deepEqual(run.server.calls.map((call) => [call.path, call.body]), [["/api/reset", { confirm: true }]]);
  assert.equal(run.seen.refreshed, 1);
  assert.equal(run.seen.shown, 1);
});
