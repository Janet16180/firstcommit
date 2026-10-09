"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { fakeServer, httpError, installBrowser, load, record } = require("./load");

installBrowser();
const { createGameApi } = load(["api.js"], ["createGameApi"]);

const REPLIES = {
  "/api/status": record("status"),
  "/api/level": record("level"),
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
  "/api/press": record("press"),
  "/api/scene": {},
  "/api/language": {},
  "/api/view": {},
};

function gameApi(replies = REPLIES) {
  const server = fakeServer(replies);
  return { game: createGameApi(server.api), calls: server.calls };
}

test("each action calls its route with the body the server expects", async () => {
  const { game, calls } = gameApi();
  await game.status();
  await game.level("a level/x");
  await game.start("lvl");
  await game.step("main");
  await game.step(null);
  await game.check(null, true);
  await game.hint();
  await game.observe();
  await game.abort();
  await game.reset();
  await game.cards("cargo", 10);
  await game.cards(null, 5);
  await game.card("card-1", "The staging area");
  await game.notes("cargo");
  await game.press("alex", "push");
  await game.scene("lvl");
  await game.language("es");
  await game.view("history");
  assert.deepEqual(calls.map((call) => [call.path, call.body]), [
    ["/api/status", undefined],
    ["/api/level?id=a%20level%2Fx", undefined],
    ["/api/start", { level: "lvl" }],
    ["/api/step", { answer: "main" }],
    ["/api/step", { answer: null }],
    ["/api/check", { answer: null, auto: true }],
    ["/api/hint", {}],
    ["/api/observe", undefined],
    ["/api/abort", {}],
    ["/api/reset", { confirm: true }],
    ["/api/cards?chapter=cargo&limit=10", undefined],
    ["/api/cards?limit=5", undefined],
    ["/api/card", { id: "card-1", reply: "The staging area" }],
    ["/api/notes?chapter=cargo", undefined],
    ["/api/press", { person: "alex", button: "push" }],
    ["/api/scene", { level: "lvl" }],
    ["/api/language", { language: "es" }],
    ["/api/view", { view: "history" }],
  ]);
});

test("every sample record is accepted as it is", async () => {
  const { game } = gameApi();
  assert.deepEqual(await game.status(), record("status"));
  assert.deepEqual(await game.observe(), record("observation"));
  assert.deepEqual(await game.cards(null, 3), record("cards"));
  assert.equal(await game.abort(), "sample-second");
  assert.deepEqual(await game.check(null, false), record("check_solved"));
  assert.deepEqual(await game.press("alex", "push"), record("press"));
  for (const action of ["level", "start", "step", "hint", "notes"]) await game[action]("x");
  await game.card("x", "y");
});

test("a quest step must carry its More as text blocks", async () => {
  const level = record("level");
  level.steps[0].more = "plain";
  const { game } = gameApi({ ...REPLIES, "/api/level": level });
  await assert.rejects(game.level("x"), /steps\[0\]\.more should be a list/);
});

test("an unsolved check and an empty observation are accepted", async () => {
  const observation = { ...record("observation"), github: null, events: [], project: record("snapshots").empty };
  const { game } = gameApi({ "/api/check": record("check_unsolved"), "/api/observe": observation });
  assert.equal((await game.check("x", false)).solved, false);
  assert.equal((await game.observe()).github, null);
});

test("a step's reply says whether the player's work is lost", async () => {
  const step = record("step");
  delete step.lost;
  await assert.rejects(gameApi({ "/api/step": step }).game.step(null), /\/api\/step.*lost/);
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

test("the game's language is English or Spanish", async () => {
  const status = { ...record("status"), language: "fr" };
  await assert.rejects(gameApi({ "/api/status": status }).game.status(), /\/api\/status.*language should be one of en, es/);
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
  const { game } = gameApi({ "/api/notes": { chapter: "cargo" } });
  await assert.rejects(game.notes("cargo"), (error) => error.status === undefined && /\/api\/notes/.test(error.message));
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

/* The reply of `route` after `change` edits a copy of its sample record. */
async function refused(route, change, call) {
  const reply = structuredClone(REPLIES[route]);
  change(reply);
  const { game } = gameApi({ ...REPLIES, [route]: reply });
  return assert.rejects(call(game));
}

test("the map's records must carry each mission's command and stars, each sector's blurb and the command collection", async () => {
  await refused("/api/status", (status) => delete status.chapters[1].levels[0].command, (game) => game.status());
  await refused("/api/status", (status) => (status.chapters[1].levels[0].stars = "two"), (game) => game.status());
  await refused("/api/status", (status) => delete status.chapters[0].blurb, (game) => game.status());
  await refused("/api/status", (status) => delete status.collection, (game) => game.status());
  await refused("/api/status", (status) => (status.collection[0].text = "plain"), (game) => game.status());
});

test("a level must carry its command, its par, its scene and whether it was seen, and its card", async () => {
  await refused("/api/level", (level) => delete level.command, (game) => game.level("x"));
  await refused("/api/level", (level) => delete level.par, (game) => game.level("x"));
  await refused("/api/level", (level) => delete level.scene_seen, (game) => game.level("x"));
  await refused("/api/level", (level) => delete level.card, (game) => game.level("x"));
  await refused("/api/level", (level) => (level.scene[0].art = "volcano"), (game) => game.level("x"));
});

test("a level must say the view it opens on and the views already born, from the ladder", async () => {
  await refused("/api/level", (level) => delete level.view, (game) => game.level("x"));
  await refused("/api/level", (level) => (level.view = "bridge"), (game) => game.level("x"));
  await refused("/api/level", (level) => delete level.views_seen, (game) => game.level("x"));
  await refused("/api/level", (level) => (level.views_seen = ["station", "deck"]), (game) => game.level("x"));
  await refused("/api/level", (level) => (level.view = "band"), (game) => game.level("x"));
  const banded = gameApi({ ...REPLIES, "/api/level": { ...record("level"), views_seen: ["station", "crew", "band", "tape"] } }).game;
  assert.deepEqual((await banded.level("x")).views_seen, ["station", "crew", "band", "tape"]);
  await refused("/api/level", (level) => (level.view = "tape"), (game) => game.level("x"));
  await refused("/api/level", (level) => delete level.tape, (game) => game.level("x"));
  for (const view of ["station", "crew", "history", "sides", "blackbox", "board", "focus"]) {
    const { game } = gameApi({ ...REPLIES, "/api/level": { ...record("level"), view } });
    assert.equal((await game.level("x")).view, view);
  }
});

test("the status says whether the game runs in dev mode", async () => {
  const { game } = gameApi();
  assert.equal((await game.status()).dev, false);
  await refused("/api/status", (status) => delete status.dev, (api) => api.status());
});

test("in dev mode a level carries its solution: the lines to type, the answers by step and to its own question", async () => {
  const { game } = gameApi();
  const { solution } = await game.level("x");
  assert.deepEqual(solution.lines, ["git add map.txt", "git commit -m \"Add the map\""]);
  assert.equal(solution.answers.guess, "It comes with you");
  assert.equal(solution.answer, null);
  const unsolved = gameApi({ ...REPLIES, "/api/level": { ...record("level"), solution: null } }).game;
  assert.equal((await unsolved.level("x")).solution, null);
  const unknown = gameApi({ ...REPLIES, "/api/level": { ...record("level"), solution: { lines: [], answers: { count: null }, answer: "Robin" } } }).game;
  assert.equal((await unknown.level("x")).solution.answers.count, null);
  await refused("/api/level", (level) => delete level.solution, (api) => api.level("x"));
  await refused("/api/level", (level) => (level.solution.lines = "git add ."), (api) => api.level("x"));
  await refused("/api/level", (level) => (level.solution.answers.guess = 3), (api) => api.level("x"));
});

test("a scene's pictures are the ones the artist has drawn", async () => {
  for (const art of ["space", "timeline", "terminal", "planet", "flag", "zones", "conveyor", "meteor", "simulator"]) {
    const level = { ...record("level"), scene: [{ ...record("level").scene[0], art }] };
    const { game } = gameApi({ ...REPLIES, "/api/level": level });
    assert.equal((await game.level("x")).scene[0].art, art);
  }
});

test("the level in progress must say the commands typed and the stars still in play", async () => {
  await refused("/api/start", (active) => delete active.commands, (game) => game.start("x"));
  await refused("/api/start", (active) => delete active.stars, (game) => game.start("x"));
});

test("a check must say the stars won and the new card, which may be null", async () => {
  const { game: api } = gameApi({ ...REPLIES, "/api/check": { ...record("check_unsolved"), stars: 0, new_card: null } });
  assert.equal((await api.check(null, false)).new_card, null);
  await refused("/api/check", (check) => delete check.stars, (game) => game.check(null, false));
  await refused("/api/check", (check) => (check.new_card = { level: "x" }), (game) => game.check(null, false));
});

test("an observation must carry Rama's reactions, each with its line, a known mood and text", async () => {
  await refused("/api/observe", (observation) => delete observation.reactions, (game) => game.observe());
  await refused("/api/observe", (observation) => (observation.reactions[0].mood = "happy"), (game) => game.observe());
  await refused("/api/observe", (observation) => delete observation.reactions[0].line, (game) => game.observe());
});

test("an observation gives each conflicted file's two sides, who wrote them and the base, a deleted side or a missing base as null", async () => {
  const { game } = gameApi();
  const [conflict] = (await game.observe()).conflicts;
  assert.equal(conflict.path, "docking.txt");
  assert.deepEqual(conflict.them, { label: "scout", author: "Alex", lines: ["Dock at bay 4"] });
  const deleted = gameApi({ ...REPLIES, "/api/observe": { ...record("observation"), conflicts: [{ ...conflict, you: { ...conflict.you, lines: null }, base: null }] } }).game;
  assert.equal((await deleted.observe()).conflicts[0].you.lines, null);
  await refused("/api/observe", (seen) => delete seen.conflicts, (api) => api.observe());
  await refused("/api/observe", (seen) => delete seen.conflicts[0].them.author, (api) => api.observe());
  await refused("/api/observe", (seen) => (seen.conflicts[0].base = "Dock at bay 2"), (api) => api.observe());
});

test("an observation gives HEAD's moves, newest first, and the commits only those moves still hold", async () => {
  const { game } = gameApi();
  const seen = await game.observe();
  assert.equal(seen.reflog[0].message, "commit: Add the route");
  assert.equal(seen.reflog.at(-1).old, "");
  const ghost = { ...record("observation").project.commits[0] };
  const haunted = gameApi({ ...REPLIES, "/api/observe": { ...record("observation"), ghosts: [ghost] } }).game;
  assert.deepEqual((await haunted.observe()).ghosts, [ghost]);
  await refused("/api/observe", (obs) => delete obs.reflog, (api) => api.observe());
  await refused("/api/observe", (obs) => delete obs.reflog[0].message, (api) => api.observe());
  await refused("/api/observe", (obs) => (obs.ghosts = [{ hash: "a" }]), (api) => api.observe());
});

test("a reaction may carry a moment the page knows, or none", async () => {
  const observation = record("observation");
  for (const moment of ["secret-leak", "launch", "junk-flood", "force-break", "unreviewed-main"]) {
    observation.reactions[0].moment = moment;
    const { game } = gameApi({ ...REPLIES, "/api/observe": observation });
    assert.equal((await game.observe()).reactions[0].moment, moment);
  }
  await refused("/api/observe", (seen) => delete seen.reactions[0].moment, (api) => api.observe());
  await refused("/api/observe", (seen) => (seen.reactions[0].moment = "fireworks"), (api) => api.observe());
  await refused("/api/observe", (seen) => (seen.reactions[0].moment = "search-beam"), (api) => api.observe());
});

test("a quest step may be a choice, with its options as text to show and a value to send back", async () => {
  const level = record("level");
  level.steps[0] = { ...level.steps[0], kind: "choice", choices: [{ value: "a", text: [{ kind: "para", spans: [{ text: "A", code: false, em: false }] }] }] };
  const { game } = gameApi({ ...REPLIES, "/api/level": level });
  assert.equal((await game.level("x")).steps[0].choices[0].value, "a");
  await refused("/api/level", (view) => delete view.steps[0].choices, (api) => api.level("x"));
  await refused("/api/level", (view) => (view.steps[0].choices = [{ value: "a" }]), (api) => api.level("x"));
});

test("a challenge is marked on the map and on its level, whose card may be null until solved", async () => {
  const { game } = gameApi({ ...REPLIES, "/api/level": { ...record("level"), challenge: true, card: null } });
  assert.equal((await game.level("x")).card, null);
  await refused("/api/level", (view) => delete view.challenge, (api) => api.level("x"));
  await refused("/api/status", (status) => delete status.chapters[1].levels[0].challenge, (api) => api.status());
});

test("the level in progress and a step's result say which goals are done", async () => {
  await refused("/api/start", (active) => delete active.done, (api) => api.start("x"));
  await refused("/api/step", (step) => (step.done = "look"), (api) => api.step(null));
});

test("a check says whether the player's work is lost for good", async () => {
  await refused("/api/check", (check) => delete check.lost, (api) => api.check(null, false));
});

test("a snapshot names the remotes its repository knows, each with its address", async () => {
  const observation = record("observation");
  delete observation.project.remotes;
  await assert.rejects(gameApi({ "/api/observe": observation }).game.observe(), /project\.remotes/);
});

test("a level says its teaching pictures and its challenge's chart, or null, and each step what it rings", async () => {
  const { game } = gameApi();
  const level = await game.level("x");
  assert.equal(level.pictures.large, "chain");
  assert.ok(level.target.commits.length > 0);
  assert.deepEqual(level.steps[0].look, ["HEAD"]);
  const plain = gameApi({ ...REPLIES, "/api/level": { ...record("level"), pictures: null, target: null } }).game;
  assert.equal((await plain.level("x")).pictures, null);
  await refused("/api/level", (body) => delete body.pictures, (api) => api.level("x"));
  await refused("/api/level", (body) => (body.pictures.large = "tape"), (api) => api.level("x"));
  await refused("/api/level", (body) => (body.pictures.small = "movelog"), (api) => api.level("x"));
  await refused("/api/level", (body) => delete body.pictures.whatif, (api) => api.level("x"));
  await refused("/api/level", (body) => delete body.target, (api) => api.level("x"));
  await refused("/api/level", (body) => (body.target.names = []), (api) => api.level("x"));
  await refused("/api/level", (body) => delete body.steps[0].look, (api) => api.level("x"));
});

test("an observation carries the desk's texts, git's graph or null, and each reflog line as git prints it", async () => {
  const { game } = gameApi();
  const observation = await game.observe();
  assert.ok(Array.isArray(observation.texts));
  assert.ok(observation.reflog.every((entry) => typeof entry.line === "string"));
  const graphless = gameApi({ ...REPLIES, "/api/observe": { ...record("observation"), graph: null, texts: [] } }).game;
  assert.equal((await graphless.observe()).graph, null);
  await refused("/api/observe", (body) => delete body.texts, (api) => api.observe());
  await refused("/api/observe", (body) => delete body.graph, (api) => api.observe());
  await refused("/api/observe", (body) => delete body.reflog[0].line, (api) => api.observe());
});

const Pg = require("./playground-records");

test("the playground's calls go to their own routes with the bodies the server expects", async () => {
  const { game, calls } = gameApi({ ...REPLIES, "/api/playground": Pg.playground(), "/api/playground/start": Pg.playground({ start: "lost" }), "/api/playground/prefs": Pg.playground({ prefs: { view: "chain", alex: true, whose: "alex" } }), "/api/playground/observe": Pg.observation() });
  assert.deepEqual(await game.playground(), Pg.playground());
  await game.playgroundStart("lost");
  await game.playgroundPrefs({ view: "chain", alex: true, whose: "alex" });
  assert.deepEqual(await game.playgroundObserve(), Pg.observation());
  assert.deepEqual(calls.map((call) => [call.path, call.body]), [
    ["/api/playground", undefined],
    ["/api/playground/start", { start: "lost" }],
    ["/api/playground/prefs", { view: "chain", alex: true, whose: "alex" }],
    ["/api/playground/observe", undefined],
  ]);
});

test("a playground with no start yet, and an observation without Alex, are accepted", async () => {
  const { game } = gameApi({ "/api/playground": Pg.playground({ start: null }), "/api/playground/observe": Pg.observation({ alex: null, github: null }) });
  assert.equal((await game.playground()).current, null);
  assert.equal((await game.playgroundObserve()).alex, null);
});

test("a start must say its blurb, its banner, the view it opens on, the chapters it uses and whether it shows Alex and has a mothership", async () => {
  for (const [field, value] of [["blurb", null], ["banner", 1], ["view", "station"], ["uses", "Collisions"], ["alex", "yes"], ["mothership", null]]) {
    const reply = Pg.playground();
    reply.starts[2][field] = value;
    const { game } = gameApi({ "/api/playground": reply });
    await assert.rejects(game.playground(), new RegExp(`starts\\[2\\]\\.${field}`), field);
  }
});

test("each person in the playground's observation carries the conflict markers the server parsed, block by block", async () => {
  const good = Pg.observation({ you: Pg.person({ marked: [Pg.marked()] }) });
  const { game } = gameApi({ "/api/playground/observe": good });
  assert.deepEqual((await game.playgroundObserve()).you.marked, [Pg.marked()]);
  const bad = structuredClone(good);
  bad.you.marked[0].parts[1].kind = "middle";
  await assert.rejects(gameApi({ "/api/playground/observe": bad }).game.playgroundObserve(), /you\.marked\[0\]\.parts\[1\]\.kind/);
  const noRepository = Pg.observation({ you: Pg.person({ graph: null }) });
  assert.equal((await gameApi({ "/api/playground/observe": noRepository }).game.playgroundObserve()).you.graph, null);
  const untyped = Pg.observation();
  delete untyped.alex.typed;
  await assert.rejects(gameApi({ "/api/playground/observe": untyped }).game.playgroundObserve(), /alex\.typed/);
});

test("a click-to-keep write names the person, the file, the text it was read from and a choice per block", async () => {
  const { game, calls } = gameApi({ "/api/playground/resolve": { file: Pg.marked() } });
  assert.deepEqual(await game.playgroundResolve({ person: "you", file: "checklist.txt", read: "r1", choices: ["yours", "both"] }), { file: Pg.marked() });
  await assert.rejects(gameApi({ "/api/playground/resolve": { file: null } }).game.playgroundResolve({ person: "you", file: "x", read: "r", choices: [] }), /file/);
  assert.deepEqual(calls.map((call) => [call.path, call.body]), [["/api/playground/resolve", { person: "you", file: "checklist.txt", read: "r1", choices: ["yours", "both"] }]]);
});

test("a level's merge panel write names the file, the text it was read from and a choice per block", async () => {
  const { game, calls } = gameApi({ "/api/resolve": { file: Pg.marked() } });
  assert.deepEqual(await game.resolve({ file: "launch.txt", read: "r1", choices: ["theirs", "both"] }), { file: Pg.marked() });
  await assert.rejects(gameApi({ "/api/resolve": { file: null } }).game.resolve({ file: "x", read: "r", choices: [] }), /file/);
  assert.deepEqual(calls.map((call) => [call.path, call.body]), [["/api/resolve", { file: "launch.txt", read: "r1", choices: ["theirs", "both"] }]]);
});

test("a level's observation carries its files in conflict as the merge panel reads them", async () => {
  const observation = { ...record("observation"), marked: [Pg.marked()] };
  assert.deepEqual(await gameApi({ "/api/observe": observation }).game.observe(), observation);
  await assert.rejects(gameApi({ "/api/observe": { ...record("observation"), marked: [{ path: "x" }] } }).game.observe(), /marked/);
});

test("the game's own playground records are accepted as they are", async () => {
  const { game } = gameApi({ "/api/playground": record("playground"), "/api/playground/observe": record("playground_observation"), "/api/playground/resolve": record("resolve") });
  assert.deepEqual(await game.playground(), record("playground"));
  assert.deepEqual(await game.playgroundObserve(), record("playground_observation"));
  assert.deepEqual(await game.playgroundResolve({ person: "you", file: "checklist.txt", read: "r", choices: ["yours"] }), record("resolve"));
});
