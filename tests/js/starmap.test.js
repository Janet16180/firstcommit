"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { fakeServer, installBrowser, load, record, settle } = require("./load");

const document = installBrowser();
const { StarMap, createGameApi, Dom } = load(["dom.js", "strings.js", "markup.js", "art-pixels.js", "art-sprites.js", "art-sky.js", "api.js", "progress.js", "dialog.js", "starmap.js"], ["StarMap", "createGameApi", "Dom"]);

function starMap(status = record("status")) {
  const server = fakeServer({ "/api/reset": {} });
  const seen = { refreshed: 0, shown: 0 };
  const prefButtons = () => [Dom.el("button", { class: "pref pref-theme" }, "Look: system")];
  const ctx = { game: createGameApi(server.api), status: () => status, refresh: async () => (seen.refreshed += 1), reload: () => (seen.shown += 1), prefButtons };
  const view = StarMap.create(ctx);
  document.body.replaceChildren(view.element);
  return { view, server, seen, q: (selector) => view.element.querySelector(selector), all: (selector) => [...view.element.querySelectorAll(selector)] };
}

const withoutActive = () => ({ ...record("status"), active: null });

test("the head shows Rama, the game's name and what it is", () => {
  const run = starMap();
  assert.ok(run.q(".map-top svg.art-rama"));
  assert.equal(run.q(".map-title").textContent, "First Commit");
  assert.match(run.q(".map-lede").textContent, /real terminal/);
});

test("the bar counts the missions done, offers the cards due and holds the look and sound buttons", () => {
  const run = starMap();
  assert.equal(run.all(".counter")[1].textContent, "Missions 1/2");
  assert.equal(run.q('.map-bar a[href="#/cards"]').textContent, "Review 4 cards");
  assert.ok(run.q(".map-bar .pref-theme"));
});

test("with no cards due there is no review button", () => {
  const run = starMap({ ...record("status"), cards_due: 0 });
  assert.equal(run.q('.map-bar a[href="#/cards"]'), null);
});

test("each chapter is a sector in order; one with missions has a star field with its planet and numbered nodes", () => {
  const run = starMap();
  assert.deepEqual(run.all(".sector .snum").map((node) => node.textContent), ["Sector 1", "Sector 2", "Sector 3"]);
  const sector = run.all(".sector")[1];
  assert.equal(sector.querySelector("h2").textContent, "The three areas");
  assert.ok(sector.querySelector(".field svg.art-field"));
  assert.ok(sector.querySelector(".field svg.art-planet"));
  assert.ok(sector.querySelector(".route polyline"));
  assert.deepEqual([...sector.querySelectorAll(".node")].map((node) => node.textContent), ["2.1", "2.2"]);
});

test("a chapter with no missions yet is a sector coming soon, with nothing to click", () => {
  const run = starMap();
  const soon = run.all(".sector")[0];
  assert.ok(soon.classList.contains("is-soon"));
  assert.equal(soon.querySelector(".soon-field").textContent, "Coming soon");
  assert.equal(soon.querySelector(".node"), null);
});

test("done missions are marked, and Rama hovers over the mission in progress", () => {
  const run = starMap();
  const [first, second] = run.all(".node");
  assert.ok(first.classList.contains("is-done"));
  assert.equal(first.getAttribute("aria-label"), "Mission 2.1: Your first commit, done");
  assert.ok(second.querySelector("svg.art-rama"));
  assert.equal(first.querySelector("svg.art-rama"), null);
});

test("with no mission in progress Rama hovers over the next one not done", () => {
  const status = withoutActive();
  status.chapters[1].levels[0].done = false;
  const run = starMap(status);
  assert.ok(run.all(".node")[0].querySelector("svg.art-rama"));
});

test("the card shows the mission in progress first, and continues it", () => {
  const run = starMap();
  assert.equal(run.q(".card-num").textContent, "Sector 2, mission 2.2");
  assert.equal(run.q(".card-title").textContent, "A message that helps");
  const play = run.q(".mission-card a.btn");
  assert.equal(play.textContent, "Continue the mission");
  assert.equal(play.getAttribute("href"), "#/level/sample-second");
  assert.ok(run.all(".node")[1].classList.contains("is-selected"));
});

test("choosing another mission shows it on the card, warning that starting it ends the one in progress", () => {
  const run = starMap();
  run.all(".node")[0].click();
  assert.equal(run.q(".card-title").textContent, "Your first commit");
  assert.equal(run.q(".mission-card a.btn").textContent, "Play again");
  assert.match(run.q(".card-note").textContent, /ends “A message that helps”, which is in progress/);
  assert.ok(run.all(".node")[0].classList.contains("is-selected"));
  assert.equal(run.all(".node")[1].classList.contains("is-selected"), false);
});

test("a mission not started yet is started from the card", () => {
  const run = starMap(withoutActive());
  assert.equal(run.q(".mission-card a.btn").textContent, "Start the mission");
  assert.equal(run.q(".card-note").textContent, "");
});

test("a map with no missions at all shows no card", () => {
  const run = starMap({ ...withoutActive(), chapters: [{ id: "start", title: "Soon", levels: [], cards: 0 }] });
  assert.equal(run.q(".mission-card"), null);
});

test("a sector with cards links its notes and its cards", () => {
  const run = starMap();
  const links = [...run.all(".sector")[1].querySelectorAll(".sector-links a")].map((link) => link.getAttribute("href"));
  assert.deepEqual(links, ["#/notes/basics", "#/cards/basics"]);
});

test("nothing on the map is a typed star or icon character", () => {
  const run = starMap();
  assert.doesNotMatch(run.view.element.textContent, /[☀-➿⭐]/);
});

test("erasing all progress asks first, then resets and shows the fresh map", async () => {
  const run = starMap();
  run.q(".erase").click();
  document.body.querySelector("dialog button.is-confirm").click();
  await settle();
  assert.deepEqual(run.server.calls.map((call) => [call.path, call.body]), [["/api/reset", { confirm: true }]]);
  assert.equal(run.seen.refreshed, 1);
  assert.equal(run.seen.shown, 1);
});

test("the bar counts the stars won out of three per mission, with a drawn star", () => {
  const run = starMap();
  const counter = run.q(".stars-won");
  assert.equal(counter.getAttribute("aria-label"), "2 of 6 stars");
  assert.ok(counter.querySelector("svg.art-star"));
  assert.equal(counter.querySelector("b").textContent, "2/6");
});

test("each sector says in one line what it teaches", () => {
  const run = starMap();
  assert.equal(run.all(".sector-blurb")[0].textContent, "What Git and GitHub are, and your first clone.");
});

test("the card shows the mission's command and its best stars", () => {
  const run = starMap();
  run.all(".node")[0].click();
  assert.equal(run.q(".card-meta code").textContent, "git init");
  assert.equal(run.q(".card-meta .art-stars").getAttribute("aria-label"), "2 of 3 stars");
});

test("the bar links the field guide", () => {
  const run = starMap();
  assert.equal(run.q(".field-guide-open").getAttribute("href"), "#/guide");
});

test("a challenge is a boss node, and its card keeps the command hidden until it is done", () => {
  const status = record("status");
  status.chapters[1].levels[1] = { ...status.chapters[1].levels[1], challenge: true };
  const run = starMap(status);
  const boss = run.all(".node")[1];
  assert.ok(boss.classList.contains("is-boss"));
  assert.match(boss.getAttribute("aria-label"), /^Challenge 2\.2/);
  assert.equal(run.q(".card-meta code"), null);
  assert.match(run.q(".card-num").textContent, /challenge 2\.2/);
});
