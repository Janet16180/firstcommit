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
  "/api/guide": record("guide"),
  "/api/press": record("press"),
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
  await game.guide();
  await game.press("alex", "push");
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
    ["/api/guide", undefined],
    ["/api/press", { person: "alex", button: "push" }],
  ]);
});

test("every sample record is accepted as it is", async () => {
  const { game } = gameApi();
  assert.deepEqual(await game.status(), record("status"));
  assert.deepEqual(await game.observe(), record("observation"));
  assert.deepEqual(await game.cards(null, 3), record("cards"));
  assert.equal(await game.abort(), "sample-second");
  assert.deepEqual(await game.check(null, false), record("check_solved"));
  assert.deepEqual(await game.guide(), record("guide"));
  assert.deepEqual(await game.press("alex", "push"), record("press"));
  for (const action of ["level", "lesson", "start", "step", "hint", "notes"]) await game[action]("x");
  await game.card("x", "y");
});

test("a lesson slide may show the places", async () => {
  const lesson = record("lesson");
  lesson.slides[2].view = "places";
  const { game } = gameApi({ ...REPLIES, "/api/lesson": lesson });
  assert.equal((await game.lesson("x")).slides[2].view, "places");
});

test("a lesson slide must tell what its commands changed, as the feed does", async () => {
  const lesson = record("lesson");
  delete lesson.slides[0].events;
  const { game } = gameApi({ ...REPLIES, "/api/lesson": lesson });
  await assert.rejects(game.lesson("x"), /slides\[0\]\.events should be a list/);
});

test("a lesson slide and a quest step must carry their More as text blocks", async () => {
  const lesson = record("lesson");
  delete lesson.slides[1].more;
  const level = record("level");
  level.steps[0].more = "plain";
  const { game } = gameApi({ ...REPLIES, "/api/lesson": lesson, "/api/level": level });
  await assert.rejects(game.lesson("x"), /slides\[1\]\.more should be a list/);
  await assert.rejects(game.level("x"), /steps\[0\]\.more should be a list/);
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

test("an observation tells the lines typed in the game's terminal and how each ended", async () => {
  const { game } = gameApi({ "/api/observe": record("observation") });
  assert.deepEqual((await game.observe()).commands, [{ line: "git add README.md", status: 0 }]);
});

test("an observation without the typed lines, or with a line missing its status, is refused", async () => {
  const missing = record("observation");
  delete missing.commands;
  await assert.rejects(gameApi({ "/api/observe": missing }).game.observe(), /\/api\/observe\.commands should be a list/);
  const noStatus = record("observation");
  delete noStatus.commands[0].status;
  await assert.rejects(gameApi({ "/api/observe": noStatus }).game.observe(), /commands\[0\]\.status should be/);
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

test("each guide figure must carry its repository before and after the change, and the change's commands", async () => {
  for (const field of ["before", "after", "transcript"]) {
    const guide = record("guide");
    delete guide.merge[field];
    const { game } = gameApi({ "/api/guide": guide });
    await assert.rejects(game.guide(), new RegExp(`/api/guide\\.merge\\.${field} should be`), field);
  }
  const { game } = gameApi({ "/api/guide": [record("guide").commit] });
  await assert.rejects(game.guide(), /\/api\/guide should be an object/);
});

test("an observation must carry the teammate's clone, or null without a playground, and its events apart", async () => {
  for (const field of ["teammate", "teammate_events"]) {
    const observation = record("observation");
    delete observation[field];
    await assert.rejects(gameApi({ "/api/observe": observation }).game.observe(), new RegExp(`/api/observe\\.${field} should be`), field);
  }
  const withTeammate = { ...record("observation"), teammate: record("snapshots").one };
  assert.deepEqual(await gameApi({ "/api/observe": withTeammate }).game.observe(), withTeammate);
});

test("a press must say who pressed which button, what ran and what it printed, and carry the lab after it", async () => {
  for (const field of ["person", "button", "command", "status", "output"]) {
    const pressed = record("press");
    delete pressed.press[field];
    await assert.rejects(gameApi({ "/api/press": pressed }).game.press("alex", "push"), new RegExp(`/api/press\\.press\\.${field} should be`), field);
  }
  for (const field of ["before", "observation", "explanation", "fix", "fix_line"]) {
    const pressed = record("press");
    delete pressed[field];
    await assert.rejects(gameApi({ "/api/press": pressed }).game.press("alex", "push"), new RegExp(`/api/press\\.${field} should be`), field);
  }
  const offered = record("press");
  offered.fix = "rebase";
  await assert.rejects(gameApi({ "/api/press": offered }).game.press("alex", "push"), /\/api\/press\.fix should be one of/);
  const stranger = record("press");
  stranger.press.person = "bob";
  await assert.rejects(gameApi({ "/api/press": stranger }).game.press("alex", "push"), /press\.person should be one of you, alex/);
});

test("a press names its button by one of the playground's ids", async () => {
  const pressing = (button) => {
    const pressed = record("press");
    pressed.press.button = button;
    return gameApi({ "/api/press": pressed }).game.press("you", button);
  };
  assert.equal((await pressing("add:notes.txt")).press.button, "add:notes.txt");
  for (const button of ["edit", "add:you.txt", "rebase", "keep-ours:"]) await assert.rejects(pressing(button), /press\.button should be one of/, button);
});

test("an observation carries each person's buttons, by person, each with its id, label, line and why it is off", async () => {
  const observation = record("press").observation;
  assert.deepEqual(Object.keys(observation.buttons), ["you", "alex"]);
  const observe = (changed) => gameApi({ "/api/observe": changed }).game.observe();
  assert.deepEqual(await observe({ ...record("observation"), buttons: {} }), { ...record("observation"), buttons: {} });
  const missing = record("observation");
  delete missing.buttons;
  await assert.rejects(observe(missing), /\/api\/observe\.buttons should be/);
  await assert.rejects(observe({ ...observation, buttons: { bob: observation.buttons.you } }), /buttons's key should be one of you, alex/);
  for (const field of ["id", "label", "line", "off"]) {
    const changed = record("press").observation;
    delete changed.buttons.alex[0][field];
    await assert.rejects(observe(changed), new RegExp(`buttons\\.alex\\[0\\]\\.${field} should be`), field);
  }
});
