"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { createClock, installBrowser, load, settle } = require("./load");

const document = installBrowser();
const { Completion } = load(["dom.js", "strings.js", "markup.js", "art-pixels.js", "art-sprites.js", "art-sky.js", "completion.js"], ["Completion"]);

const para = (text) => [{ kind: "para", spans: [{ text, code: false }] }];

test("the band crosses the screen with the title and the mission, with sparks, then leaves by itself", async () => {
  const clock = createClock();
  let over = false;
  Completion.band({ title: "Mission complete", subtitle: "Mission 2.1: First cargo", stars: 2, timers: clock, reducedMotion: false }).then(() => (over = true));
  const layer = document.body.querySelector(".band-layer");
  assert.equal(layer.querySelector(".band h2").textContent, "Mission complete");
  assert.equal(layer.querySelector(".band small").textContent, "Mission 2.1: First cargo");
  assert.ok(layer.querySelector(".art-sparks"));
  assert.equal(layer.querySelector(".band .art-stars").getAttribute("aria-label"), "2 of 3 stars");
  assert.equal(layer.getAttribute("aria-hidden"), "true");
  await clock.advance(1749);
  assert.equal(over, false);
  await clock.advance(1);
  assert.equal(over, true);
  assert.equal(document.body.querySelector(".band-layer"), null);
});

test("a click ends the band at once", async () => {
  const clock = createClock();
  let over = false;
  Completion.band({ title: "Mission complete", subtitle: "", stars: 3, timers: clock, reducedMotion: false }).then(() => (over = true));
  document.body.querySelector(".band-layer").click();
  await settle();
  assert.equal(over, true);
  assert.equal(document.body.querySelector(".band-layer"), null);
  assert.equal(clock.pending(), 0);
});

test("with reduced motion there is no band", async () => {
  const clock = createClock();
  await Completion.band({ title: "Mission complete", subtitle: "", stars: 3, timers: clock, reducedMotion: true });
  assert.equal(document.body.querySelector(".band-layer"), null);
});

test("the dock names the mission, shows its lesson and offers Retry, Map and the next mission", () => {
  let retried = 0;
  const dock = Completion.dock({ title: "Mission complete: mission 2.1", stars: 3, lesson: para("git add loads a file."), next: { href: "#/level/two", title: "Second" }, onRetry: () => (retried += 1) });
  assert.equal(dock.getAttribute("role"), "status");
  assert.equal(dock.querySelector(".dock-title").textContent, "Mission complete: mission 2.1");
  assert.equal(dock.querySelector(".dock-lesson").textContent, "git add loads a file.");
  const actions = [...dock.querySelectorAll(".dock-actions .btn")];
  assert.deepEqual(actions.map((action) => action.textContent), ["Retry", "Map", "Next mission"]);
  assert.equal(actions[1].getAttribute("href"), "#/");
  assert.equal(actions[2].getAttribute("href"), "#/level/two");
  assert.ok(actions[2].classList.contains("btn-primary"));
  actions[0].click();
  assert.equal(retried, 1);
});

test("without a next mission the map is the way on, and a missing lesson is said plainly", () => {
  const dock = Completion.dock({ title: "Done", stars: 1, lesson: null, next: null, onRetry: () => {} });
  const actions = [...dock.querySelectorAll(".dock-actions .btn")];
  assert.deepEqual(actions.map((action) => action.textContent), ["Retry", "Map"]);
  assert.ok(actions[1].classList.contains("btn-primary"));
  assert.equal(dock.querySelector(".dock-lesson").textContent, "This mission's lesson is not available.");
});

test("the dock shows the stars won, what the play paid and the new command card", () => {
  const card = { level: "x", command: "git init", text: para("Makes a repository.") };
  const dock = Completion.dock({ title: "Done", stars: 2, lesson: null, reward: "+150 XP", card, next: null, onRetry: () => {} });
  assert.equal(dock.querySelector(".dock-stars .art-stars").getAttribute("aria-label"), "2 of 3 stars");
  assert.equal(dock.querySelector(".dock-xp").textContent, "+150 XP");
  assert.equal(dock.querySelector(".dock-card").textContent, "New card in your collection: git init");
});

test("without a reward line or a new card the dock leaves them out", () => {
  const dock = Completion.dock({ title: "Done", stars: 2, lesson: null, next: null, onRetry: () => {} });
  assert.equal(dock.querySelector(".dock-xp"), null);
  assert.equal(dock.querySelector(".dock-card"), null);
});

test("a challenge's dock is the gold one", () => {
  assert.ok(Completion.dock({ title: "Done", stars: 3, lesson: null, challenge: true, next: null, onRetry: () => {} }).classList.contains("is-challenge"));
});

test("lost work takes the dock's place with the game's message, Retry and Map, and no stars", () => {
  let retried = 0;
  const panel = Completion.lost({ message: para("The edit was never saved, so Git cannot bring it back."), onRetry: () => (retried += 1) });
  assert.ok(panel.classList.contains("is-lost"));
  assert.equal(panel.getAttribute("role"), "alert");
  assert.match(panel.querySelector(".dock-lesson").textContent, /never saved/);
  assert.equal(panel.querySelector(".art-stars"), null);
  const actions = [...panel.querySelectorAll(".dock-actions .btn")];
  assert.deepEqual(actions.map((action) => action.textContent), ["Retry", "Map"]);
  actions[0].click();
  assert.equal(retried, 1);
});
