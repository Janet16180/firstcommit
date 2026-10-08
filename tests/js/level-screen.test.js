"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { createClock, fakeServer, httpError, installBrowser, load, record, settle } = require("./load");

const document = installBrowser({ reducedMotion: true });
const { LevelScreen, createGameApi } = load(
  ["dom.js", "strings.js", "markup.js", "art-pixels.js", "art-sprites.js", "art-sky.js", "art-scenes.js", "art-moments.js", "api.js", "progress.js", "poll.js", "typed.js", "zones.js", "zone-panel.js", "mission.js", "comms.js", "completion.js", "scene.js", "moment-layer.js", "view-tabs.js", "strip.js", "sides.js", "tape.js", "births.js", "art-infographics.js", "infographic-text.js", "field-guide.js", "level-screen.js"],
  ["LevelScreen", "createGameApi"],
);

const para = (text) => [{ kind: "para", spans: [{ text, code: false }] }];
const correct = (step, questDone = false, done = []) => ({ correct: true, message: para("Right."), step, quest_done: questDone, done, lost: false });

/* The sample level, its scene and its view already seen unless the test says otherwise. */
const seenLevel = () => ({ ...record("level"), scene_seen: true, views_seen: ["station", "crew", "history"] });
const quiet = () => ({ ...record("observation"), commands: [], reactions: [] });

/* A level screen for the sample level; `active` is the level in progress as the status first says
   (null: none), `recounted` the level in progress the dashboard gives after typed lines. */
function screen({ active = record("active"), replies = {}, levelId = "sample-second", recounted = null, dev = false } = {}) {
  const clock = createClock();
  let status = { ...record("status"), active, dev };
  const seen = { sounds: [], attached: 0, detached: 0, typed: [], ran: [], finished: [], reloads: 0 };
  const server = fakeServer({
    "/api/level": seenLevel(),
    "/api/scene": {},
    "/api/view": {},
    "/api/start": { ...record("active"), step: 0 },
    /* A line the terminal ran is told by the next observation once it has finished, as the game tells it. */
    "/api/observe": () => ({ ...quiet(), commands: seen.finished.splice(0).map((line) => ({ line, status: 0 })) }),
    "/api/step": record("step"),
    "/api/check": record("check_unsolved"),
    "/api/hint": record("hint"),
    ...replies,
  });
  const ctx = {
    game: createGameApi(server.api),
    status: () => status,
    refresh: async () => {
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
      detach: () => (seen.detached += 1), type: (text) => seen.typed.push(text), run: (line) => {
        seen.ran.push(line);
        clock.setTimeout(() => seen.finished.push(line), 300);
      } },
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

/* The sample level with a second watch goal after its first, so a goal met by a typed line has one after it. */
function twoWatches(reactions) {
  const level = seenLevel();
  level.steps = [...level.steps, { ...level.steps[2], id: "commit" }];
  const met = { ...correct(3, false, ["look", "status", "stage"]), message: para("Staged. Now seal it.") };
  return screen({ active: { ...record("active"), step: 2 }, replies: { "/api/level": level, "/api/step": met, "/api/observe": { ...quiet(), reactions } } });
}

test("a goal met by a line Rama warns about leaves the warning on Rama's line, and says itself under the next goal", async () => {
  const run = twoWatches([{ line: "git add .", mood: "warn", text: para("The keys rode along."), moment: null }]);
  await settle();
  assert.equal(run.q(".comms-text").textContent, "The keys rode along.");
  assert.equal(run.q(".comms").dataset.mood, "warn");
  assert.equal(run.q(".goal.is-current .goal-note").textContent, "Staged. Now seal it.");
  run.view.dispose();
});

test("a goal met by a line whose reaction plays a moment leaves that reaction on Rama's line", async () => {
  const run = twoWatches([{ line: "git status", mood: "ok", text: para("Why secrets stay out."), moment: "secret-leak" }]);
  await settle();
  assert.equal(run.q(".comms-text").textContent, "Why secrets stay out.");
  assert.equal(run.q(".goal.is-current .goal-note").textContent, "Staged. Now seal it.");
  run.view.dispose();
});

/* Two watch goals where the first is met only on the second ask, and the observations are `first`
   once, then `later` for good. */
function metLate(first, later = quiet()) {
  const level = seenLevel();
  level.steps = [...level.steps, { ...level.steps[2], id: "commit" }];
  let asked = 0;
  let observed = 0;
  const met = { ...correct(3, false, ["look", "status", "stage"]), message: para("Staged. Now seal it.") };
  const waiting = { ...record("step"), step: 2, message: para("Stage the notes.") };
  const waitingNext = { ...record("step"), step: 3, message: para("Seal the capsule.") };
  const step = () => {
    asked += 1;
    if (asked === 1) return waiting;
    return asked === 2 ? met : waitingNext;
  };
  return screen({ active: { ...record("active"), step: 2, steps: 4 }, replies: { "/api/level": level, "/api/step": step, "/api/observe": () => ((observed += 1) === 1 ? first : later) } });
}

test("a goal met a tick after a line Rama warned about leaves the warning on Rama's line", async () => {
  const run = metLate({ ...quiet(), commands: [{ line: "git add .", status: 0 }], reactions: [{ line: "git add .", mood: "warn", text: para("The keys rode along."), moment: null }] });
  await settle();
  await run.clock.advance(1500);
  assert.equal(run.q(".comms-text").textContent, "The keys rode along.");
  assert.equal(run.q(".comms").dataset.mood, "warn");
  assert.equal(run.q(".goal.is-current .goal-note").textContent, "Staged. Now seal it.");
  run.view.dispose();
});

test("a met goal's note stays under the next goal until the player types again", async () => {
  const typed = { ...quiet(), commands: [{ line: "git add .", status: 0 }], reactions: [{ line: "git add .", mood: "warn", text: para("The keys rode along."), moment: null }] };
  const run = metLate(typed);
  await settle();
  await run.clock.advance(1500);
  await run.clock.advance(1500);
  await settle();
  assert.equal(run.q(".goal.is-current .goal-note").textContent, "Staged. Now seal it.");
  run.view.dispose();
});

test("once the player types again, the next goal's own note replaces the met goal's", async () => {
  const typed = (line) => ({ ...quiet(), commands: [{ line, status: 0 }], reactions: [{ line, mood: "warn", text: para("The keys rode along."), moment: null }] });
  const run = metLate(typed("git add ."), typed("git log"));
  await settle();
  await run.clock.advance(1500);
  await run.clock.advance(1500);
  await settle();
  assert.equal(run.q(".goal.is-current .goal-note").textContent, "Seal the capsule.");
  run.view.dispose();
});

test("a goal met by a line with a plain reaction is said on Rama's line, as before", async () => {
  const run = twoWatches([{ line: "git add notes.txt", mood: "ok", text: para("On the dock."), moment: null }]);
  await settle();
  assert.equal(run.q(".comms-text").textContent, "Staged. Now seal it.");
  assert.ok(!run.q(".goal-note"));
  run.view.dispose();
});

test("a solve by a line whose reaction plays a moment keeps that reaction on Rama's line, and the band waits for the moment", async () => {
  const reactions = [{ line: "git pull", mood: "ok", text: para("The whole ship is in your station."), moment: "launch" }];
  const run = screen({ active: { ...record("active"), step: 3, auto_check: true }, replies: { "/api/check": record("check_solved"), "/api/observe": { ...quiet(), reactions } } });
  await settle();
  await settle();
  assert.equal(run.q(".comms-text").textContent, "The whole ship is in your station.");
  assert.ok(!document.querySelector(".band-layer"));
  assert.ok(!run.q(".dock"));
  await run.clock.advance(10000);
  assert.ok(Boolean(run.q(".dock")));
  assert.equal(run.q(".comms-text").textContent, "The whole ship is in your station.");
  run.view.dispose();
});

test("a solve that comes a tick after a moment's reaction, while the moment plays, leaves that reaction on Rama's line", async () => {
  let observed = 0;
  let checks = 0;
  const reactions = [{ line: "git pull", mood: "ok", text: para("The whole ship is in your station."), moment: "launch" }];
  const run = screen({
    active: { ...record("active"), step: 3, auto_check: true },
    replies: {
      "/api/observe": () => ({ ...quiet(), reactions: (observed += 1) === 1 ? reactions : [] }),
      "/api/check": () => ((checks += 1) === 1 ? record("check_unsolved") : record("check_solved")),
    },
  });
  await settle();
  await run.clock.advance(1500);
  assert.ok(checks >= 2);
  assert.equal(run.q(".comms-text").textContent, "The whole ship is in your station.");
  await run.clock.advance(10000);
  assert.ok(Boolean(run.q(".dock")));
  run.view.dispose();
});

test("a plain reaction that replaces a moment's while it still plays frees Rama's line, so the solve that follows is said", async () => {
  let observed = 0;
  let checks = 0;
  const moment = [{ line: "git status", mood: "warn", text: para("Why junk stays out."), moment: "launch" }];
  const plain = [{ line: "git add notes.txt", mood: "ok", text: para("Staged."), moment: null }];
  const run = screen({
    active: { ...record("active"), step: 3, auto_check: true },
    replies: {
      "/api/observe": () => {
        observed += 1;
        const reactions = [moment, plain][observed - 1] || [];
        return { ...quiet(), reactions, commands: reactions.map(({ line }) => ({ line, status: 0 })) };
      },
      "/api/check": () => ((checks += 1) < 2 ? record("check_unsolved") : record("check_solved")),
    },
  });
  await settle();
  await run.clock.advance(1500);
  await settle();
  assert.equal(said(run), record("check_solved").message[0].spans.map((span) => span.text).join(""));
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
  assert.ok(run.seen.sounds.includes("complete"));
  const calls = run.server.calls.length;
  await run.clock.advance(10000);
  assert.equal(run.server.calls.length, calls);
  assert.equal(run.seen.detached, 0);
  run.view.dispose();
});

test("a solve says the game's verdict on Rama's line, so an earlier nudge never outlives it", async () => {
  const run = screen({ active: { ...record("active"), step: 3, auto_check: true }, replies: { "/api/check": record("check_solved") } });
  await settle();
  await settle();
  assert.match(run.q(".comms").textContent, /Solved\./);
  assert.equal(run.q(".comms").dataset.mood, "ok");
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
  const reactions = [{ line: "git status", mood: "err", text: para("Not a repository yet."), moment: null }, { line: "git init", mood: "ok", text: para("Flag planted."), moment: null }];
  const run = screen({ replies: { "/api/observe": { ...quiet(), reactions } } });
  await settle();
  assert.equal(run.q(".comms-text").textContent, "Not a repository yet.Flag planted.");
  assert.equal(run.q(".comms").dataset.mood, "ok");
  run.view.dispose();
});

test("two typed lines with the same reaction have Rama say it once", async () => {
  const reactions = [{ line: "git log", mood: "info", text: para("Your history."), moment: null }, { line: "git log notes.txt", mood: "info", text: para("Your history."), moment: null }];
  const run = screen({ replies: { "/api/observe": { ...quiet(), reactions } } });
  await settle();
  assert.equal(run.q(".comms-text").textContent, "Your history.");
  run.view.dispose();
});

test("a reaction that carries a moment plays it over the zones, once however often the game repeats it", async () => {
  const reactions = [{ line: "git push", mood: "ok", text: para("Both halves are up."), moment: "launch" }];
  const run = screen({ replies: { "/api/observe": { ...quiet(), reactions } } });
  await settle();
  await run.clock.advance(4000);
  const layer = run.q(".moment-layer");
  assert.equal(layer.hidden, false);
  assert.equal(run.all(".moment-layer .art-moment").length, 1);
  assert.ok(Boolean(run.q(".moment-layer .art-moment--launch")));
  await run.clock.advance(6000);
  assert.equal(layer.hidden, true);
  run.view.dispose();
});

test("a reaction without a moment leaves the zones uncovered", async () => {
  const reactions = [{ line: "git status", mood: "info", text: para("Clean."), moment: null }];
  const run = screen({ replies: { "/api/observe": { ...quiet(), reactions } } });
  await settle();
  assert.equal(run.q(".moment-layer").hidden, true);
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

test("the lab is watched only once the scene is over, so what a level stages first happens in view", async () => {
  const run = screen({ replies: { "/api/level": record("level") } });
  await settle();
  await run.clock.advance(5000);
  assert.equal(run.routes().includes("/api/observe"), false);
  document.body.querySelector("dialog.cutscene .cs-skip").click();
  await settle();
  assert.ok(run.routes().includes("/api/observe"));
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

test("a typed line gets a blip, a failed one a buzz, a ticked goal and a lost star their own sounds", async () => {
  const typed = (status) => ({ ...quiet(), commands: [{ line: "git status", status }] });
  const ok = screen({ replies: { "/api/observe": typed(0) } });
  await settle();
  assert.ok(ok.seen.sounds.includes("command"));
  ok.view.dispose();
  const failed = screen({ replies: { "/api/observe": typed(128) }, recounted: { ...record("active"), stars: 2 } });
  await settle();
  await settle();
  assert.ok(failed.seen.sounds.includes("failed"));
  assert.ok(failed.seen.sounds.includes("starlost"));
  failed.view.dispose();
  const goal = screen({ active: { ...record("active"), step: 2 }, replies: { "/api/step": correct(3, true) } });
  await settle();
  assert.ok(goal.seen.sounds.includes("goal"));
  goal.view.dispose();
});

test("a prediction sends the choice, shows the reveal on Rama's line in a neutral mood, and moves on", async () => {
  const level = seenLevel();
  level.steps[1] = { ...level.steps[1], kind: "choice", question: para("Where does it go?"), choices: [{ value: "dock", text: para("The dock") }, { value: "vault", text: para("The vault") }] };
  const reveal = { ...correct(2), message: para("It waits on the dock until you commit.") };
  const run = screen({ replies: { "/api/level": level, "/api/step": reveal } });
  await settle();
  run.all(".goal.is-current .goal-choice")[1].click();
  await settle();
  assert.deepEqual(run.server.calls.at(-1).body, { answer: "vault" });
  assert.equal(run.q(".comms-text").textContent, "It waits on the dock until you commit.");
  assert.equal(run.q(".comms").dataset.mood, "info");
  assert.ok(run.all(".goal")[2].classList.contains("is-current"));
  assert.equal(run.seen.sounds.includes("correct"), false);
  run.view.dispose();
});

test("a line typed while a prediction waits, that the game has nothing to say about, gets a nudge to answer it first", async () => {
  const level = seenLevel();
  level.steps[1] = { ...level.steps[1], kind: "choice", question: para("Where does it go?"), choices: [{ value: "dock", text: para("The dock") }] };
  const run = screen({ replies: { "/api/level": level, "/api/observe": { ...quiet(), commands: [{ line: "git fetch", status: 0 }] } } });
  await settle();
  assert.equal(run.q(".comms-text").textContent, "Answer the prediction first: the goals after it wait for your answer.");
  assert.equal(run.q(".comms").dataset.mood, "info");
  run.view.dispose();
});

test("a challenge says so in the head, hides its command until solved, watches every goal, and docks in gold", async () => {
  const level = { ...seenLevel(), challenge: true, card: null };
  const run = screen({ active: { ...record("active"), step: 0, done: [] }, replies: { "/api/level": level, "/api/step": { ...record("step"), step: 0, done: [] } } });
  await settle();
  assert.equal(run.q(".hud-num").textContent, "Challenge 2.2");
  assert.equal(run.q(".hud-command").hidden, true);
  assert.ok(run.view.element.classList.contains("is-challenge"));
  assert.deepEqual(run.routes(), ["/api/level", "/api/observe", "/api/step"]);
  run.view.dispose();
});

test("a challenge's goals tick in the order they are met", async () => {
  const level = { ...seenLevel(), challenge: true, card: null };
  const run = screen({ active: { ...record("active"), step: 0, done: [] }, replies: { "/api/level": level, "/api/step": { ...correct(1), done: ["stage"] } } });
  await settle();
  assert.deepEqual(run.all(".goal").map((goal) => goal.classList.contains("is-done")), [false, false, true]);
  run.view.dispose();
});

test("in a challenge a met goal ticks, and Rama only says a part is in place, never what comes next", async () => {
  const level = { ...seenLevel(), challenge: true, card: null };
  const run = screen({ active: { ...record("active"), step: 0, done: [] }, replies: { "/api/level": level, "/api/step": { ...correct(1), done: ["stage"], message: para("The next goal is not met yet.") } } });
  await settle();
  assert.ok(run.seen.sounds.includes("goal"));
  assert.equal(run.q(".comms-text").textContent, "One part of the end state is in place.");
  assert.equal(run.q(".comms").dataset.mood, "ok");
  run.view.dispose();
});

test("a solved challenge docks in gold", async () => {
  const level = { ...seenLevel(), challenge: true, card: null };
  const run = screen({ active: { ...record("active"), step: 3, auto_check: true }, replies: { "/api/level": level, "/api/check": record("check_solved") } });
  await settle();
  await settle();
  assert.ok(run.q(".dock").classList.contains("is-challenge"));
  assert.match(run.q(".dock-title").textContent, /^Challenge complete/);
  run.view.dispose();
});

test("work lost while a goal is watched stops the level and shows the failure with Retry", async () => {
  const lost = { ...record("step"), step: 2, correct: false, lost: true, message: para("The keys are in a commit now.") };
  const run = screen({ active: { ...record("active"), step: 2 }, replies: { "/api/step": lost } });
  await settle();
  await settle();
  assert.ok(run.q(".dock.is-lost"));
  assert.match(run.q(".dock.is-lost").textContent, /The keys are in a commit now\./);
  assert.ok(run.seen.sounds.includes("wrong"));
  const calls = run.server.calls.length;
  await run.clock.advance(10000);
  assert.equal(run.server.calls.length, calls);
  run.view.dispose();
});

test("when the work is lost, the goal's note goes: the lost panel and Rama say what happened", async () => {
  let ticks = 0;
  const reply = () => {
    ticks += 1;
    return ticks === 1 ? { ...record("step"), step: 2, correct: false, message: para("Unstage the keys.") } : { ...record("step"), step: 2, correct: false, lost: true, message: para("The keys are in a commit now.") };
  };
  const run = screen({ active: { ...record("active"), step: 2 }, replies: { "/api/step": reply } });
  try {
    await settle();
    assert.match(run.q(".goal.is-current .goal-note").textContent, /Unstage the keys/);
    await run.clock.advance(2000);
    await settle();
    assert.ok(run.q(".dock.is-lost"));
    assert.equal(Boolean(run.q(".goal-note")), false);
  } finally {
    run.view.dispose();
  }
});

test("work lost for good stops the level and shows the failure with Retry, even from an automatic check", async () => {
  const lost = { ...record("check_unsolved"), lost: true, message: para("The edit is gone for good.") };
  const run = screen({ active: { ...record("active"), step: 3, auto_check: true }, replies: { "/api/check": lost } });
  await settle();
  await settle();
  assert.ok(run.q(".dock.is-lost"));
  assert.equal(run.q(".dock.is-lost .art-stars"), null);
  assert.ok(run.seen.sounds.includes("wrong"));
  const calls = run.server.calls.length;
  await run.clock.advance(10000);
  assert.equal(run.server.calls.length, calls);
  run.q(".dock.is-lost .btn-primary").click();
  await settle();
  assert.equal(run.routes().at(-1), "/api/start");
  run.view.dispose();
});

/* The sample level opening on `view`, with `seen` the views already born. */
function viewing(view, seen, replies = {}) {
  return screen({ replies: { "/api/level": { ...seenLevel(), view, views_seen: seen }, ...replies } });
}

const tabs = (run) => run.all(".view-tab").map((tab) => tab.dataset.view);
const shown = (run) => run.q(".sky").dataset.view;
const yours = (run) => run.all(".strip").find((strip) => !strip.classList.contains("is-band"));
const chosen = (run) => run.all(".view-tab").find((tab) => tab.getAttribute("aria-selected") === "true").dataset.view;

test("a level that opens on history folds your station into the strip, with a tab back to it", async () => {
  const run = viewing("history", ["station", "history"]);
  await settle();
  assert.equal(shown(run), "history");
  assert.deepEqual(tabs(run), ["station", "history"]);
  assert.equal(chosen(run), "history");
  assert.equal(yours(run).hidden, false);
  assert.deepEqual([...yours(run).querySelectorAll(".strip-card")].map((card) => card.dataset.zone), ["workshop", "dock", "vault", "remote"]);
  run.view.dispose();
});

test("the station's tab unfolds the strip back into the zones, and the history tab folds it again", async () => {
  const run = viewing("history", ["station", "history"]);
  await settle();
  run.q('.view-tab[data-view="station"]').click();
  assert.equal(shown(run), "station");
  assert.equal(yours(run).hidden, true);
  run.q('.view-tab[data-view="history"]').click();
  assert.equal(shown(run), "history");
  assert.equal(yours(run).hidden, false);
  run.view.dispose();
});

test("a tapped card of the strip expands your station again", async () => {
  const run = viewing("history", ["station", "history"]);
  await settle();
  run.q('.strip-card[data-zone="vault"]').click();
  assert.equal(shown(run), "station");
  assert.equal(chosen(run), "station");
  run.view.dispose();
});

test("a level on your station alone shows no tab row and no strip", async () => {
  const run = viewing("station", ["station"]);
  await settle();
  assert.equal(shown(run), "station");
  assert.equal(run.q(".view-tabs").hidden, true);
  assert.equal(yours(run).hidden, true);
  run.view.dispose();
});

test("a view not born yet and with no birth to play is marked born when its level opens; one already born is not marked again", async () => {
  const run = viewing("station", []);
  await settle();
  assert.deepEqual(run.server.calls.filter((call) => call.path === "/api/view").map((call) => call.body), [{ view: "station" }]);
  run.view.dispose();
  const again = viewing("history", ["station", "history"]);
  await settle();
  assert.ok(!again.routes().includes("/api/view"));
  again.view.dispose();
});

const said = (run) => run.q(".comms-text").textContent;
const marked = (run) => run.server.calls.filter((call) => call.path === "/api/view").map((call) => call.body);

test("history is born once your vault holds commits: the fold and the unroll with Rama's lines, then its tab, and the game is told", async () => {
  const run = viewing("history", ["station"]);
  await settle();
  assert.equal(shown(run), "fold");
  assert.equal(said(run), "You know every room now.");
  assert.equal(run.q(".view-tabs").hidden, true);
  assert.deepEqual(marked(run), []);
  await run.clock.advance(2600);
  assert.equal(shown(run), "history");
  assert.equal(said(run), "Here's the chart of every course.");
  await run.clock.advance(2600);
  assert.deepEqual(marked(run), [{ view: "history" }]);
  assert.deepEqual(tabs(run), ["station", "history"]);
  assert.equal(chosen(run), "history");
  run.view.dispose();
});

test("a goal met as history is born goes under the next goal, and the line typed has its say first, so Rama's birth lines are heard", async () => {
  const level = { ...seenLevel(), view: "history", views_seen: ["station"] };
  level.steps = [...level.steps, { ...level.steps[2], id: "read" }];
  const met = { ...correct(3, false, ["look", "status", "stage"]), message: para("Cloned.") };
  const cloned = { ...record("observation"), commands: [{ line: "git clone x project", status: 0 }], reactions: [{ line: "git clone x project", mood: "ok", text: para("A copy came down."), moment: null }] };
  const run = screen({ active: { ...record("active"), step: 2, steps: 4 }, replies: { "/api/level": level, "/api/step": met, "/api/observe": cloned } });
  await settle();
  assert.equal(said(run), "You know every room now.");
  assert.equal(run.q(".goal.is-current .goal-note").textContent, "Cloned.");
  run.view.dispose();
});

test("while your vault is empty, a level whose history is not born yet stays on your station", async () => {
  const empty = { ...quiet(), project: record("snapshots").unborn };
  const run = viewing("history", ["station"], { "/api/observe": empty });
  await settle();
  await run.clock.advance(6000);
  assert.equal(shown(run), "station");
  assert.deepEqual(marked(run), []);
  run.view.dispose();
});

test("a view the page cannot draw yet opens on your station", async () => {
  const run = viewing("board", ["station", "history", "board"]);
  await settle();
  assert.equal(shown(run), "station");
  assert.deepEqual(tabs(run), ["station", "history"]);
  run.view.dispose();
});

test("in a level with a teammate the crew view stands in for your station's tab", async () => {
  const run = viewing("history", ["station", "crew", "history"], { "/api/observe": { ...record("press").observation, commands: [], reactions: [] } });
  await settle();
  assert.deepEqual(tabs(run), ["crew", "history"]);
  run.q('.view-tab[data-view="crew"]').click();
  assert.equal(shown(run), "crew");
  run.view.dispose();
});

test("in a crew level, history flattens Alex's station into the band along the top; the crew view brings it back", async () => {
  const run = viewing("history", ["station", "crew", "history", "band"], { "/api/observe": { ...record("press").observation, commands: [], reactions: [] } });
  await settle();
  const band = run.q(".strip.is-band");
  assert.equal(band.hidden, false);
  assert.deepEqual([...band.querySelectorAll(".strip-card")].map((card) => card.dataset.zone), ["workshop", "dock", "vault"]);
  assert.equal(band.querySelector('.strip-card[data-zone="workshop"] .strip-count').textContent, "2");
  run.q('.view-tab[data-view="crew"]').click();
  assert.equal(band.hidden, true);
  run.view.dispose();
});

test("without a teammate there is no band", async () => {
  const run = viewing("history", ["station", "history"]);
  await settle();
  assert.equal(run.q(".strip.is-band").hidden, true);
  run.view.dispose();
});

const crewQuiet = () => ({ ...record("press").observation, commands: [], reactions: [] });

test("the band is born the first time a crew level opens on another view: the crew view flattens, Rama says so, and the game is told", async () => {
  const run = viewing("history", ["station", "crew", "history"], { "/api/observe": crewQuiet() });
  await settle();
  assert.equal(shown(run), "flatten");
  assert.equal(said(run), "Alex's station, flattened into a band: it still shows what reaches them.");
  assert.equal(run.q(".strip.is-band").hidden, false);
  assert.deepEqual(marked(run), []);
  await run.clock.advance(2600);
  assert.equal(shown(run), "history");
  assert.deepEqual(marked(run), [{ view: "band" }]);
  assert.deepEqual(tabs(run), ["crew", "history"]);
  run.view.dispose();
});

test("no band is born before the crew view, in a level that opens on the crew view, or once it was", async () => {
  for (const [view, seen] of [["history", ["station", "history"]], ["crew", ["station", "crew"]], ["history", ["station", "crew", "history", "band"]]]) {
    const run = viewing(view, seen, { "/api/observe": crewQuiet() });
    await settle();
    await run.clock.advance(3000);
    assert.notEqual(shown(run), "flatten", `${view} ${seen}`);
    assert.deepEqual(marked(run), [], `${view} ${seen}`);
    run.view.dispose();
  }
});

/* An observation with docking.txt in conflict, as git leaves it after a merge stops. */
function conflicted() {
  const one = record("snapshots").one;
  const project = { ...one, operation: "merge", files: [{ ...one.files[0], path: "docking.txt", conflicted: true, index_change: "modified" }] };
  return { ...record("observation"), project, commands: [], reactions: [] };
}

test("two sides take the zones' place under your strip, one book per conflicted file", async () => {
  const run = viewing("sides", ["station", "history", "sides"], { "/api/observe": conflicted() });
  await settle();
  assert.equal(shown(run), "sides");
  assert.equal(run.q(".sides").hidden, false);
  assert.equal(yours(run).hidden, false);
  assert.equal(run.q(".sides-path").textContent, "docking.txt");
  assert.deepEqual(tabs(run), ["station", "history", "sides"]);
  run.q('.view-tab[data-view="history"]').click();
  assert.equal(run.q(".sides").hidden, true);
  run.view.dispose();
});

test("two sides are born when the first conflict appears, then get their tab and the game is told", async () => {
  const run = viewing("sides", ["station", "history"], { "/api/observe": conflicted() });
  await settle();
  assert.equal(shown(run), "sides");
  assert.equal(said(run), "Your scanner has a docking mode: both sides, line by line.");
  assert.deepEqual(marked(run), []);
  await run.clock.advance(2600);
  assert.deepEqual(marked(run), [{ view: "sides" }]);
  assert.deepEqual(tabs(run), ["station", "history", "sides"]);
  run.view.dispose();
});

test("before any conflict, a level whose two sides are not born yet stays on your station", async () => {
  const run = viewing("sides", ["station", "history"]);
  await settle();
  await run.clock.advance(3000);
  assert.equal(shown(run), "station");
  assert.equal(run.q(".sides").hidden, true);
  run.view.dispose();
});

test("the black box keeps the zones on stage, framing what Git keeps, and is born as its level opens", async () => {
  const run = viewing("blackbox", ["station", "history"]);
  await settle();
  assert.equal(shown(run), "blackbox");
  assert.equal(said(run), "Before anyone travels in time: a flight recorder.");
  assert.equal(yours(run).hidden, true);
  await run.clock.advance(2600);
  assert.deepEqual(marked(run), [{ view: "blackbox" }]);
  assert.deepEqual(tabs(run), ["station", "history", "blackbox"]);
  assert.equal(chosen(run), "blackbox");
  run.view.dispose();
});

/* A level that shows the tape, opening on `view` with `seen` born; `observe` replies to each look. */
function taped(view, seen, observe = () => quiet()) {
  return screen({ replies: { "/api/level": { ...seenLevel(), view, views_seen: seen, tape: true }, "/api/observe": observe } });
}

test("a level that does not show the tape has none, even on history with the tape born", async () => {
  const run = viewing("history", ["station", "history", "tape"]);
  await settle();
  assert.equal(run.q(".tape").hidden, true);
  run.view.dispose();
});

test("in a level that shows it, the tape runs under history and the black box, and leaves with your station", async () => {
  const run = taped("history", ["station", "history", "blackbox", "tape"], () => record("observation"));
  await settle();
  assert.equal(run.q(".tape").hidden, false);
  assert.equal(run.all(".tape-tick").length, record("observation").reflog.length);
  run.q('.view-tab[data-view="blackbox"]').click();
  assert.equal(run.q(".tape").hidden, false);
  run.q('.view-tab[data-view="station"]').click();
  assert.equal(run.q(".tape").hidden, true);
  run.view.dispose();
});

test("the tape is born on the level's first move of HEAD: it appears in place, Rama says so, and the game is told", async () => {
  const moved = { ...record("observation"), reflog: [{ old: record("observation").reflog[0].new, new: record("observation").reflog[1].new, message: "reset: moving to HEAD~1" }, ...record("observation").reflog] };
  let looks = 0;
  const run = taped("history", ["station", "history", "blackbox"], () => ((looks += 1) === 1 ? record("observation") : moved));
  await settle();
  assert.equal(run.q(".tape").hidden, true);
  await run.clock.advance(1500);
  assert.equal(run.q(".tape").hidden, false);
  assert.equal(said(run), "The flight recorder keeps a tape: every move of HEAD, even to capsules no label holds.");
  assert.equal(shown(run), "history");
  assert.deepEqual(marked(run), []);
  await run.clock.advance(2600);
  assert.deepEqual(marked(run), [{ view: "tape" }]);
  assert.deepEqual(tabs(run), ["station", "history", "blackbox"]);
  run.view.dispose();
});

test("in a crew level the black box keeps to your row, framed, and Alex goes into the band above it", async () => {
  const run = viewing("blackbox", ["station", "crew", "history", "blackbox", "band"], { "/api/observe": crewQuiet() });
  await settle();
  assert.equal(shown(run), "blackbox");
  assert.equal(run.q(".station"), null);
  assert.ok(run.q(".viz-kept"));
  assert.equal(run.q(".strip.is-band").hidden, false);
  assert.equal(yours(run).hidden, true);
  run.q('.view-tab[data-view="crew"]').click();
  assert.ok(run.q(".station.is-mirror"));
  assert.equal(run.q(".strip.is-band").hidden, true);
  run.view.dispose();
});

/* A dev-mode screen on the sample level at its answer goal, whose solution is `solution`. */
function solving(solution, replies = {}) {
  return screen({ dev: true, replies: { "/api/level": { ...seenLevel(), solution }, "/api/step": correct(2), ...replies } });
}

test("out of dev mode the head has no Solve button", async () => {
  const run = screen();
  await settle();
  assert.equal(run.q(".hud .solve").hidden, true);
  run.view.dispose();
});

test("in dev mode, Solve runs the solution's lines in the terminal one at a time, each once the last has run", async () => {
  const run = solving({ lines: ["git status", "git add notes.txt"], answers: { status: "notes.txt" }, answer: null });
  await settle();
  assert.equal(run.q(".hud .solve").hidden, false);
  run.q(".hud .solve").click();
  await run.clock.advance(100);
  assert.deepEqual(run.seen.ran, ["git status"]);
  await run.clock.advance(1000);
  assert.deepEqual(run.seen.ran, ["git status"]);
  await run.clock.advance(2000);
  assert.deepEqual(run.seen.ran, ["git status", "git add notes.txt"]);
  run.view.dispose();
});

test("Solve answers a goal that asks before it runs a line, so the goals after it see the lines", async () => {
  const order = [];
  const run = solving({ lines: ["git add notes.txt"], answers: { status: "notes.txt" }, answer: null }, {
    "/api/step": (body) => {
      order.push(`step ${body.answer}`);
      return correct(2);
    },
  });
  await settle();
  const ran = run.ctx.terminal.run;
  run.ctx.terminal.run = (line) => {
    order.push(`run ${line}`);
    ran(line);
  };
  run.q(".hud .solve").click();
  await run.clock.advance(2000);
  assert.deepEqual(order.filter((item) => item !== "step null"), ["step notes.txt", "run git add notes.txt"]);
  run.view.dispose();
});

test("leaving the level stops Solve: no later line runs and the game is asked nothing more", async () => {
  const run = solving({ lines: ["git status", "git add notes.txt"], answers: { status: "notes.txt" }, answer: null });
  await settle();
  run.q(".hud .solve").click();
  await settle();
  run.view.dispose();
  const calls = run.server.calls.length;
  await run.clock.advance(5000);
  await settle();
  assert.deepEqual(run.seen.ran, ["git status"]);
  assert.equal(run.server.calls.length, calls);
});

test("after the lines, Solve answers the goals that ask, with the solution's answers read again from the game", async () => {
  let asked = 0;
  const first = { lines: ["git status"], answers: { status: null }, answer: null };
  const then = { lines: ["git status"], answers: { status: "notes.txt" }, answer: null };
  const run = screen({ dev: true, replies: { "/api/level": () => ({ ...seenLevel(), solution: (asked += 1) <= 2 ? first : then }), "/api/step": correct(2) } });
  await settle();
  run.q(".hud .solve").click();
  await run.clock.advance(2000);
  await settle();
  const steps = run.server.calls.filter((call) => call.path === "/api/step" && call.body.answer !== null);
  assert.deepEqual(steps.map((call) => call.body), [{ answer: "notes.txt" }]);
  assert.ok(run.all(".goal")[2].classList.contains("is-current"));
  run.view.dispose();
});

test("Solve ends with the level's own question, answered from the solution", async () => {
  const level = { ...seenLevel(), question: para("Who made the commit?"), placeholder: "a name", solution: { lines: [], answers: {}, answer: "Robin" } };
  const run = screen({ dev: true, active: { ...record("active"), step: 3 }, replies: { "/api/level": level, "/api/check": record("check_solved") } });
  await settle();
  run.q(".hud .solve").click();
  await run.clock.advance(1000);
  await settle();
  assert.deepEqual(run.server.calls.filter((call) => call.path === "/api/check" && !call.body.auto).map((call) => call.body), [{ answer: "Robin", auto: false }]);
  run.view.dispose();
});

test("the head opens the field guide over the level, and closing it leaves the level, its terminal and its watch as they were", async () => {
  const run = screen();
  await settle();
  const before = run.routes().length;
  run.q(".hud .guide-open").click();
  const overlay = document.querySelector("dialog.guide-overlay");
  assert.ok(overlay.open);
  assert.ok(overlay.querySelector(".field-guide h1"));
  assert.equal(overlay.querySelector('a[href="#/"]'), null);
  await run.clock.advance(1500);
  assert.ok(run.routes().length > before);
  overlay.querySelector(".guide-close").click();
  assert.equal(document.querySelector("dialog.guide-overlay"), null);
  assert.equal(run.seen.detached, 0);
  assert.ok(run.q(".hud"));
  run.view.dispose();
});

test("Escape closes the field guide like its close button", async () => {
  const run = screen();
  await settle();
  run.q(".hud .guide-open").click();
  document.querySelector("dialog.guide-overlay").close();
  assert.equal(document.querySelector("dialog.guide-overlay"), null);
  run.view.dispose();
});

test("leaving the level takes an open field guide with it", async () => {
  const run = screen();
  await settle();
  run.q(".hud .guide-open").click();
  run.view.dispose();
  assert.equal(document.querySelector("dialog.guide-overlay"), null);
});
