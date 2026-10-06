"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

const document = installBrowser({ reducedMotion: true });
const { Celebrate } = load(["dom.js", "celebrate.js"], ["Celebrate"]);

const WIN = { kicker: "Level complete", title: "Your first commit", xp: 100, firstTime: true, rankBefore: "Newcomer", rankAfter: "Committer", button: "See what you learned" };

test("a win shows the level, the XP paid and a new rank, then continues on the button", async () => {
  const done = Celebrate.show(WIN);
  const overlay = document.body.querySelector("dialog.celebration");
  assert.match(overlay.textContent, /Level complete.*Your first commit/);
  assert.match(overlay.querySelector(".celebration-xp").textContent, /\+100 XP/);
  assert.match(overlay.querySelector(".celebration-rank").textContent, /Committer/);
  assert.equal(document.activeElement, overlay.querySelector("button"));
  overlay.querySelector("button").click();
  await done;
  assert.equal(document.body.querySelector("dialog.celebration"), null);
});

test("a replay says it pays nothing, and an unchanged rank is not announced", async () => {
  const done = Celebrate.show({ ...WIN, firstTime: false, xp: 0, rankBefore: "Committer", rankAfter: "Committer" });
  const overlay = document.body.querySelector("dialog.celebration");
  assert.match(overlay.querySelector(".celebration-xp").textContent, /no XP/);
  assert.equal(overlay.querySelector(".celebration-rank").hidden, true);
  overlay.close();
  await done;
});
