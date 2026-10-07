"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { createClock, fakeServer, httpError, installBrowser, load, record, settle } = require("./load");

const document = installBrowser({ reducedMotion: true });
const { LevelScreen, createGameApi } = load(
  ["dom.js", "markup.js", "art-pixels.js", "art-sprites.js", "art-sky.js", "art-scenes.js", "api.js", "progress.js", "poll.js", "typed.js", "zones.js", "zone-panel.js", "mission.js", "comms.js", "completion.js", "collection.js", "scene.js", "level-screen.js"],
  ["LevelScreen", "createGameApi"],
);

const para = (text) => [{ kind: "para", spans: [{ text, code: false }] }];
const correct = (step, questDone = false) => ({ correct: true, message: para("Right."), step, quest_done: questDone });

/* The sample level, its scene already seen unless the test says otherwise. */
const seenLevel = () => ({ ...record("level"), scene_seen: true });
const quiet = () => ({ ...record("observation"), commands: [], reactions: [] });

/* A level screen for the sample level; `active` is the level in progress as the status first says
   (null: none), `recounted` the level in progress the dashboard gives after typed lines. */
function screen({ active = record("active"), replies = {}, levelId = "sample-second", recounted = null } = {}) {
  const clock = createClock();
  let status = { ...record("status"), active };
  const server = fakeServer({
    "/api/level": seenLevel(),
    "/api/scene": {},
    "/api/start": { ...record("active"), step: 0 },
    "/api/observe": quiet(),
    "/api/step": record("step"),
    "/api/check": record("check_unsolved"),
    "/api/hint": record("hint"),
    ...replies,
  });
  const seen = { sounds: [], attached: 0, detached: 0, typed: [], reloads: 0, refreshed: 0 };
  const ctx = {
    game: createGameApi(server.api),
    status: () => status,
    refresh: async () => {
      seen.refreshed += 1;
      if (server.calls.some((call) => call.path === "/api/start")) status = { ...status, active: record("active") };
      if (recounted) status = { ...status, active: recounted };
      return status;
    },
    reload: () => (seen.reloads += 1),
    sound: { play: (name) => seen.sounds.push(name) },
    timers: clock,
    page: document,
    reducedMotion: true,
    terminal: {
      attach: (host) => {
        seen.attached += 1;
        seen.host = host;
      },
      detach: () => (seen.detached += 1), type: (text) => seen.typed.push(text) },
    setStatus: (next) => (status = next),
  };
  const view = LevelScreen.create(ctx, levelId);
  document.body.replaceChildren(view.element);
  const routes = () => server.calls.map((call) => call.path.split("?")[0]);
  return { view, ctx, clock, server, seen, routes, q: (selector) => view.element.querySelector(selector), all: (selector) => [...view.element.querySelectorAll(selector)] };
}

test("a mission in progress opens at once: its number and title in the head, the zones, the goals, Rama and the terminal", async () => {
  const run = screen();
  await settle();
  assert.equal(run.q(".hud-num").textContent, "Mission 2.2");
  assert.equal(run.q(".hud-name").textContent, "A message that helps");
  assert.ok(run.q(".viz .zone"));
  assert.equal(run.all(".goal").length, 3);
  assert.ok(run.q(".comms"));
  assert.equal(run.seen.attached, 1);
  assert.ok(run.seen.host.classList.contains("termcol"));
  assert.deepEqual(run.routes(), ["/api/level", "/api/observe"]);
  run.view.dispose();
  assert.equal(run.seen.detached, 1);
});

test("the head leads back to the map and offers a restart, with drawn icons, never typed ones", async () => {
  const run = screen();
  await settle();
  const back = run.q(".hud a.btn");
  assert.equal(back.getAttribute("href"), "#/");
  assert.ok(back.querySelector("svg.art-icon"));
  assert.match(run.q(".hud .restart").textContent, /Restart/);
  assert.doesNotMatch(run.q(".hud").textContent, /[←-⇿☀-➿]/);
  run.view.dispose();
});

test("a mission not in progress is started first, then shown", async () => {
  const run = screen({ active: null });
  assert.match(run.q(".comms").textContent, /Preparing/);
  await settle();
  await settle();
  assert.deepEqual(run.routes().slice(0, 3), ["/api/start", "/api/level", "/api/observe"]);
  assert.deepEqual(run.server.calls[0].body, { level: "sample-second" });
  assert.equal(run.seen.attached, 1);
  run.view.dispose();
});

test("an unknown mission says there is none, with a way back to the map", async () => {
  const run = screen({ active: null, levelId: "nowhere", replies: { "/api/start": httpError(404) } });
  await settle();
  assert.match(run.view.element.textContent, /There is no mission here/);
  assert.ok(run.q('a[href="#/"]'));
  assert.equal(run.seen.attached, 0);
});

test("the zones are drawn from every observation", async () => {
  const run = screen();
  await settle();
  assert.equal(run.q('.zone[data-zone="vault"] .chash').textContent, "547cd2b");
  run.view.dispose();
});

test("a wrong answer gets the server's nudge on Rama's line", async () => {
  const run = screen();
  await settle();
  const form = run.q(".goal.is-current form");
  form.querySelector("input").value = "README.md";
  form.dispatchEvent(makeEvent("submit"));
  await settle();
  assert.deepEqual(run.server.calls.at(-1).body, { answer: "README.md" });
  assert.match(run.q(".comms").textContent, /Not quite/);
  assert.equal(run.q(".comms").dataset.mood, "err");
  assert.deepEqual(run.seen.sounds, ["wrong"]);
  run.view.dispose();
});

test("a right answer is confirmed and the next goal becomes current", async () => {
  const run = screen({ replies: { "/api/step": correct(2) } });
  await settle();
  const form = run.q(".goal.is-current form");
  form.querySelector("input").value = "notes.txt";
  form.dispatchEvent(makeEvent("submit"));
  await settle();
  assert.equal(run.q(".comms").dataset.mood, "ok");
  assert.ok(run.all(".goal")[2].classList.contains("is-current"));
  run.view.dispose();
});

test("a goal to read moves on with Continue", async () => {
  const run = screen({ active: { ...record("active"), step: 0 }, replies: { "/api/step": correct(1) } });
  await settle();
  run.q(".goal-continue").click();
  await settle();
  assert.deepEqual(run.server.calls.at(-1).body, { answer: null });
  assert.ok(run.all(".goal")[1].classList.contains("is-current"));
  run.view.dispose();
});

test("while a watch goal is current, every tick asks about it, and it passes by itself", async () => {
  let passed = false;
  const run = screen({ active: { ...record("active"), step: 2 }, replies: { "/api/step": () => (passed ? correct(3, true) : { ...record("step"), step: 2 }) } });
  await settle();
  assert.deepEqual(run.routes(), ["/api/level", "/api/observe", "/api/step"]);
  assert.equal(run.q(".comms").dataset.mood, "info");
  passed = true;
  await run.clock.advance(1500);
  assert.equal(run.all(".goal.is-done").length, 3);
  run.view.dispose();
});

test("once the quest is done the mission is checked by itself; a solve stops the polling and docks the lesson at the bottom", async () => {
  const run = screen({ active: { ...record("active"), step: 3, auto_check: true }, replies: { "/api/check": record("check_solved") } });
  await settle();
  await settle();
  const dock = run.q(".dock");
  assert.ok(dock);
  assert.equal(dock.querySelector(".dock-title").textContent, "Mission complete: mission 2.2");
  assert.match(dock.querySelector(".dock-lesson").textContent, /Git records what is staged/);
  assert.ok(run.view.element.classList.contains("is-docked"));
  assert.ok(run.seen.sounds.includes("celebrate"));
  const calls = run.server.calls.length;
  await run.clock.advance(10000);
  assert.equal(run.server.calls.length, calls);
  assert.equal(run.seen.detached, 0);
  run.view.dispose();
});

test("an automatic check that does not solve stays silent", async () => {
  const run = screen({ active: { ...record("active"), step: 3, auto_check: true } });
  await settle();
  assert.match(run.q(".comms").textContent, /Read the goals/);
  assert.deepEqual(run.seen.sounds, []);
  run.view.dispose();
});

test("the dock's Retry starts the mission again and shows it afresh", async () => {
  const run = screen({ active: { ...record("active"), step: 3, auto_check: true }, replies: { "/api/check": record("check_solved") } });
  await settle();
  await settle();
  run.q(".dock .btn").click();
  await settle();
  assert.equal(run.routes().at(-1), "/api/start");
  assert.equal(run.seen.reloads, 1);
  run.view.dispose();
});

test("Restart in the head starts the mission again", async () => {
  const run = screen();
  await settle();
  run.q(".hud .restart").click();
  await settle();
  assert.equal(run.routes().at(-1), "/api/start");
  assert.equal(run.seen.reloads, 1);
  run.view.dispose();
});

test("a hint is revealed in the panel and Rama points at it", async () => {
  const run = screen();
  await settle();
  run.q(".hint-row button").click();
  await settle();
  assert.equal(run.all(".hint-list div").length, 1);
  assert.match(run.q(".comms").textContent, /hint/);
  assert.deepEqual(run.seen.sounds, ["hint"]);
  run.view.dispose();
});

test("a command clicked in the panel is typed in the terminal", async () => {
  const run = screen();
  await settle();
  run.all(".goal")[1].querySelector("pre code").click();
  assert.deepEqual(run.seen.typed, ["git status"]);
  run.view.dispose();
});

test("a mission solved from the command line shows the dock with its lesson", async () => {
  const run = screen({ replies: { "/api/observe": httpError(409) } });
  run.ctx.setStatus({ ...record("status"), active: null, last_payout: { ...record("status").last_payout, level: "sample-second" } });
  await settle();
  await settle();
  assert.ok(run.q(".dock"));
  run.view.dispose();
});

test("a mission ended elsewhere without a solve says so on Rama's line and stops", async () => {
  const run = screen({ replies: { "/api/observe": httpError(409) } });
  await settle();
  await settle();
  assert.match(run.q(".comms").textContent, /no longer in progress/);
  assert.equal(run.q(".dock"), null);
  const calls = run.server.calls.length;
  await run.clock.advance(10000);
  assert.equal(run.server.calls.length, calls);
  run.view.dispose();
});

test("when the server does not answer Rama says so, and the page keeps trying", async () => {
  let down = true;
  const run = screen({ replies: { "/api/observe": () => (down ? httpError(0) : record("observation")) } });
  await settle();
  assert.match(run.q(".comms").textContent, /not answering/);
  down = false;
  await run.clock.advance(1500);
  assert.doesNotMatch(run.q(".comms").textContent, /not answering/);
  run.view.dispose();
});

test("the page tells the stylesheet where the terminal's column starts, so the terminal reaches the window's bottom", async () => {
  const run = screen();
  await settle();
  assert.equal(run.view.element.style["--term-top"], "0px");
  run.view.dispose();
});

test("the head shows the mission's command, the commands typed against the par plus three, and the stars in play", async () => {
  const run = screen();
  await settle();
  assert.equal(run.q(".hud-command").textContent, "git commit -m");
  assert.equal(run.q(".hud-cmds").textContent, "3 / 7 commands");
  assert.equal(run.q(".hud-stars .art-stars").getAttribute("aria-label"), "3 stars in play");
  run.view.dispose();
});

test("after typed lines the head shows the commands and stars as the game counts them, and a lost star shakes", async () => {
  const run = screen({ replies: { "/api/observe": { ...quiet(), commands: [{ line: "ls", status: 0 }] } }, recounted: { ...record("active"), commands: 8, stars: 2 } });
  await settle();
  await settle();
  assert.equal(run.q(".hud-cmds").textContent, "8 / 7 commands");
  assert.equal(run.q(".hud-stars .art-stars").getAttribute("aria-label"), "2 stars in play");
  assert.ok(run.q(".hud-stars").classList.contains("is-lost"));
  run.view.dispose();
});

test("Rama says the game's reactions to the typed lines, oldest first, in the newest one's mood", async () => {
  const reactions = [{ line: "git status", mood: "err", text: para("Not a repository yet.") }, { line: "git init", mood: "ok", text: para("Flag planted.") }];
  const run = screen({ replies: { "/api/observe": { ...quiet(), reactions } } });
  await settle();
  assert.equal(run.q(".comms-text").textContent, "Not a repository yet.Flag planted.");
  assert.equal(run.q(".comms").dataset.mood, "ok");
  run.view.dispose();
});

test("while a watch goal waits, the game's note shows under the goal, not on Rama's line", async () => {
  const run = screen({ active: { ...record("active"), step: 2 } });
  await settle();
  assert.match(run.q(".goal.is-current .goal-note").textContent, /Not quite/);
  assert.match(run.q(".comms").textContent, /Read the goals/);
  run.view.dispose();
});

test("a level's scene plays the first time it opens, and the game is told once it is over", async () => {
  const run = screen({ replies: { "/api/level": record("level") } });
  await settle();
  const dialog = document.body.querySelector("dialog.cutscene");
  assert.ok(dialog.open);
  assert.equal(run.routes().includes("/api/scene"), false);
  dialog.querySelector(".cs-skip").click();
  await settle();
  assert.deepEqual(run.server.calls.filter((call) => call.path === "/api/scene").map((call) => call.body), [{ level: "sample-second" }]);
  run.view.dispose();
});

test("a scene already seen does not play by itself; Intro plays it again without telling the game", async () => {
  const run = screen();
  await settle();
  assert.equal(document.body.querySelector("dialog.cutscene"), null);
  assert.equal(run.q(".hud .intro").hidden, false);
  run.q(".hud .intro").click();
  const dialog = document.body.querySelector("dialog.cutscene");
  assert.ok(dialog.open);
  dialog.querySelector(".cs-skip").click();
  await settle();
  assert.equal(run.routes().includes("/api/scene"), false);
  run.view.dispose();
});

test("a level without a scene has no Intro button", async () => {
  const run = screen({ replies: { "/api/level": { ...seenLevel(), scene: [] } } });
  await settle();
  assert.equal(run.q(".hud .intro").hidden, true);
  run.view.dispose();
});

test("the dock shows the stars won, what the play paid and the new command card", async () => {
  const run = screen({ active: { ...record("active"), step: 3, auto_check: true }, replies: { "/api/check": record("check_solved") } });
  await settle();
  await settle();
  const dock = run.q(".dock");
  assert.equal(dock.querySelector(".dock-stars .art-stars").getAttribute("aria-label"), "3 of 3 stars");
  assert.equal(dock.querySelector(".dock-xp").textContent, "+150 XP");
  assert.equal(dock.querySelector(".dock-card code").textContent, 'git commit -m "Message"');
  run.view.dispose();
});

test("a solve with a hint used and no XP says why", async () => {
  const solved = { ...record("check_solved"), payout: { ...record("check_solved").payout, xp: 0 } };
  const run = screen({ active: { ...record("active"), step: 3, auto_check: true, hints: 1 }, replies: { "/api/check": solved } });
  await settle();
  await settle();
  assert.equal(run.q(".dock-xp").textContent, "No XP this time: a hint was used.");
  run.view.dispose();
});
