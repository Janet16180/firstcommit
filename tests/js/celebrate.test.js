"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { createClock, installBrowser, load } = require("./load");

const document = installBrowser({ reducedMotion: true });
const { Celebrate } = load(["dom.js", "celebrate.js"], ["Celebrate"]);

const WIN = { kicker: "Level complete", title: "Your first commit", xp: 100, firstTime: true, rankBefore: "Newcomer", rankAfter: "Committer", button: "See what you learned" };

test("a win shows the level, the XP paid and a new rank, then continues on the button", async () => {
  const done = Celebrate.show(WIN);
  const overlay = document.body.querySelector("dialog.celebration");
  assert.match(overlay.textContent, /Level complete.*Your first commit/);
  assert.match(overlay.querySelector(".celebration-xp").textContent, /\+100 XP/);
  assert.match(overlay.querySelector(".celebration-rank").textContent, /Committer/);
  overlay.querySelector("button").click();
  await done;
  assert.equal(document.body.querySelector("dialog.celebration"), null);
});

test("a replay shows the XP the server paid and says it was played again; an unchanged rank is not announced", async () => {
  const done = Celebrate.show({ ...WIN, firstTime: false, xp: 30, rankBefore: "Committer", rankAfter: "Committer" });
  const overlay = document.body.querySelector("dialog.celebration");
  assert.match(overlay.querySelector(".celebration-xp").textContent, /\+30 XP/);
  assert.match(overlay.querySelector(".celebration-replay").textContent, /Played again/);
  assert.equal(overlay.querySelector(".celebration-rank").hidden, true);
  overlay.close();
  await done;
});

test("a first win does not say it was played again", async () => {
  const done = Celebrate.show(WIN);
  const overlay = document.body.querySelector("dialog.celebration");
  assert.equal(overlay.querySelector(".celebration-replay"), null);
  overlay.close();
  await done;
});

test("a key the player was typing as the card appears cannot dismiss it: focus reaches the button a moment later", async () => {
  const clock = createClock();
  const done = Celebrate.show({ ...WIN, timers: clock });
  const overlay = document.body.querySelector("dialog.celebration");
  assert.equal(document.activeElement, overlay.querySelector("h2"));
  await clock.advance(Celebrate.FOCUS_DELAY_MS);
  assert.equal(document.activeElement, overlay.querySelector("button"));
  overlay.close();
  await done;
});
