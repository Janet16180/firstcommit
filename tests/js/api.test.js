"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { fakeServer, httpError, installBrowser, load, record } = require("./load");

installBrowser();
const { createGameApi } = load(["api.js"], ["createGameApi"]);

const REPLIES = {
  "/api/status": record("status"),
  "/api/level": record("level"),
  "/api/lesson": record("lesson"),
  "/api/start": record("active"),
  "/api/step": record("step"),
  "/api/check": record("check_solved"),
  "/api/hint": record("hint"),
  "/api/observe": record("observation"),
  "/api/abort": { level: "sample-second" },
  "/api/reset": {},
  "/api/cards": { cards: record("cards") },
  "/api/card": record("card_result"),
  "/api/notes": record("notes"),
};

function gameApi(replies = REPLIES) {
  const server = fakeServer(replies);
  return { game: createGameApi(server.api), calls: server.calls };
}

test("each action calls its route with the body the server expects", async () => {
  const { game, calls } = gameApi();
  await game.status();
  await game.level("a level/x");
  await game.lesson("lvl");
  await game.start("lvl");
  await game.step("main");
  await game.step(null);
  await game.check(null, true);
  await game.hint();
  await game.observe();
  await game.abort();
  await game.reset();
  await game.cards("basics", 10);
  await game.cards(null, 5);
  await game.card("card-1", "The staging area");
  await game.notes("basics");
  assert.deepEqual(calls.map((call) => [call.path, call.body]), [
    ["/api/status", undefined],
    ["/api/level?id=a%20level%2Fx", undefined],
    ["/api/lesson?id=lvl", undefined],
    ["/api/start", { level: "lvl" }],
    ["/api/step", { answer: "main" }],
    ["/api/step", { answer: null }],
    ["/api/check", { answer: null, auto: true }],
    ["/api/hint", {}],
    ["/api/observe", undefined],
    ["/api/abort", {}],
    ["/api/reset", { confirm: true }],
    ["/api/cards?chapter=basics&limit=10", undefined],
    ["/api/cards?limit=5", undefined],
    ["/api/card", { id: "card-1", reply: "The staging area" }],
    ["/api/notes?chapter=basics", undefined],
  ]);
});

test("every sample record is accepted as it is", async () => {
  const { game } = gameApi();
  assert.deepEqual(await game.status(), record("status"));
  assert.deepEqual(await game.observe(), record("observation"));
  assert.deepEqual(await game.cards(null, 3), record("cards"));
  assert.equal(await game.abort(), "sample-second");
  assert.deepEqual(await game.check(null, false), record("check_solved"));
  for (const action of ["level", "lesson", "start", "step", "hint", "notes"]) await game[action]("x");
  await game.card("x", "y");
});

test("an unsolved check and an empty observation are accepted", async () => {
  const observation = { ...record("observation"), github: null, events: [], project: record("snapshots").empty };
  const { game } = gameApi({ "/api/check": record("check_unsolved"), "/api/observe": observation });
  assert.equal((await game.check("x", false)).solved, false);
  assert.equal((await game.observe()).github, null);
});

test("a reply missing a field is refused with the route and the field named", async () => {
  const status = record("status");
  delete status.rank.next_at;
  const { game } = gameApi({ "/api/status": status });
  await assert.rejects(game.status(), /\/api\/status.*rank\.next_at/);
});

test("a field of the wrong type is refused", async () => {
  const observation = record("observation");
  observation.project.commits[1].parents = "abc";
  const { game } = gameApi({ "/api/observe": observation });
  await assert.rejects(game.observe(), /project\.commits\[1\]\.parents should be a list/);
});

test("text with an unknown kind of block is refused", async () => {
  const hint = record("hint");
  hint.hint = [{ kind: "table" }];
  const { game } = gameApi({ "/api/hint": hint });
  await assert.rejects(game.hint(), /hint\[0\]\.kind/);
});

test("a server error keeps its HTTP status for the page to act on", async () => {
  const { game } = gameApi({ "/api/observe": httpError(409, "no level is in progress") });
  await assert.rejects(game.observe(), (error) => error.status === 409);
});

test("a contract error carries no HTTP status", async () => {
  const { game } = gameApi({ "/api/notes": { chapter: "basics" } });
  await assert.rejects(game.notes("basics"), (error) => error.status === undefined && /\/api\/notes/.test(error.message));
});

test("a level reply must carry its question, the hints shown so far and its debrief", async () => {
  for (const field of ["question", "placeholder", "hints", "debrief"]) {
    const level = record("level");
    delete level[field];
    const { game } = gameApi({ "/api/level": level });
    await assert.rejects(game.level("x"), new RegExp(`/api/level\\.${field} should be`), field);
  }
});

test("a file entry must carry its mode in each area, whether it is a repository and git status's two columns", async () => {
  for (const field of ["head_mode", "index_mode", "folder_mode", "repository", "index_change", "folder_change"]) {
    const observation = record("observation");
    delete observation.project.files[0][field];
    const { game } = gameApi({ "/api/observe": observation });
    await assert.rejects(game.observe(), new RegExp(`files\\[0\\]\\.${field} should be`), field);
  }
});

test("the level in progress must say whether the page may check it by itself", async () => {
  const active = record("active");
  delete active.auto_check;
  const { game } = gameApi({ "/api/start": active });
  await assert.rejects(game.start("x"), /\/api\/start\.auto_check should be/);
});

test("a change git status does not list is refused, so the page never shows a column it has no words for", async () => {
  const observation = record("observation");
  observation.project.files[0].folder_change = "renamed";
  const { game } = gameApi({ "/api/observe": observation });
  await assert.rejects(game.observe(), /files\[0\]\.folder_change should be/);
});

test("the dashboard must say the difficulty scale, and each card its level's name", async () => {
  const status = record("status");
  delete status.max_difficulty;
  await assert.rejects(gameApi({ "/api/status": status }).game.status(), /\/api\/status\.max_difficulty should be/);
  const cards = record("cards");
  delete cards[0].level_name;
  await assert.rejects(gameApi({ "/api/cards": { cards } }).game.cards(null, 10), /level_name should be/);
});
