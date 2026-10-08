"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { createClock, fakeServer, installBrowser, load, settle } = require("./load");
const Pg = require("./playground-records");

const document = installBrowser({ reducedMotion: true });
const { PlaygroundScreen, PlaygroundSummary, createGameApi } = load(
  ["dom.js", "strings.js", "places.js", "art-pixels.js", "art-sprites.js", "api.js", "poll.js", "typed.js", "zones.js", "zone-panel.js", "dialog.js", "keep-panel.js", "editor-strip.js", "chain.js", "folder-row.js", "desk.js", "move-log.js", "git-graph.js", "playground-summary.js", "playground-picture.js", "playground-screen.js"],
  ["PlaygroundScreen", "PlaygroundSummary", "createGameApi"],
);

/* A playground screen: `lab` answers each look at the lab (an observation, or a function giving one). */
function screen({ playground = Pg.playground(), lab = Pg.observation(), route = {}, replies = {} } = {}) {
  const clock = createClock();
  const server = fakeServer({
    "/api/playground": playground,
    "/api/playground/start": (body) => Pg.playground({ start: body.start, started: "s2" }),
    "/api/playground/prefs": {},
    "/api/playground/resolve": {},
    "/api/playground/observe": typeof lab === "function" ? lab : () => lab,
    ...replies,
  });
  const shells = { attached: [], detached: 0 };
  const playTerminals = {
    attach: (person, host, started, onTitle) => {
      shells.attached.push([person, started]);
      shells[person] = host;
      shells.titles = { ...shells.titles, [person]: onTitle };
    },
    keys: (person, keys) => (shells.keys = [...(shells.keys || []), [person, keys]]),
    detach: () => (shells.detached += 1),
    type: (person, text) => (shells.typed = [...(shells.typed || []), [person, text]]),
  };
  const ctx = { game: createGameApi(server.api), timers: clock, page: document, reducedMotion: true, playTerminals };
  const view = PlaygroundScreen.create(ctx, { view: "playground", start: null, picture: null, tryLine: null, ...route });
  document.body.replaceChildren(view.element);
  const q = (selector) => view.element.querySelector(selector);
  const all = (selector) => [...view.element.querySelectorAll(selector)];
  const calls = (path) => server.calls.filter((call) => call.path === path);
  const click = (selector) => q(selector).dispatchEvent(makeEvent("click"));
  return { view, clock, server, shells, q, all, calls, click };
}

const tabs = (run) => run.all(".pg-tab:not([hidden])").map((tab) => tab.dataset.view);
const picked = (run) => run.q(".pg-tab[aria-selected=\"true\"]").dataset.view;

test("the playground opens on the current start's own view, with its name in the head", async () => {
  const run = screen();
  await settle();
  assert.equal(run.q(".pg-title").textContent, "Playground");
  assert.equal(run.q(".pg-start").textContent, "Start branches");
  assert.equal(picked(run), "chain");
  assert.ok(run.q(".pg-picture .chain"));
});

test("Chain, History, Desk and Crew come first, Move log and Graph under More views", async () => {
  const run = screen();
  await settle();
  assert.deepEqual(run.all(".pg-tabs .pg-tab:not([hidden])").map((tab) => tab.dataset.view), ["chain", "history", "desk", "crew"]);
  assert.equal(run.q(".pg-more-button").textContent, "More views");
  assert.ok(run.q(".pg-more-list").hidden);
  run.click(".pg-more-button");
  assert.equal(run.q(".pg-more-list").hidden, false);
  assert.deepEqual(run.all(".pg-more-list .pg-tab").map((tab) => tab.textContent), ["Move log", "Graph"]);
});

test("a folder with no mothership has no History or Crew to show", async () => {
  const run = screen({ playground: Pg.playground({ start: "empty" }), lab: Pg.observation({ start: "empty", alex: null, github: null }) });
  await settle();
  assert.deepEqual(tabs(run), ["chain", "desk", "movelog", "graph"]);
  assert.equal(picked(run), "desk");
});

test("picking a view draws it and remembers it for this start", async () => {
  const run = screen();
  await settle();
  run.click(".pg-tab[data-view=\"desk\"]");
  await settle();
  assert.ok(run.q(".pg-picture .desk"));
  assert.equal(run.q(".pg-picture .chain"), null);
  run.click(".pg-more-button");
  run.click(".pg-tab[data-view=\"graph\"]");
  await settle();
  assert.ok(run.q(".pg-picture .graph"));
  assert.ok(run.q(".pg-more-list").hidden);
  assert.equal(run.q(".pg-more-button").getAttribute("aria-current"), "true");
  assert.deepEqual(run.calls("/api/playground/prefs").map((call) => call.body), [{ view: "desk", alex: false, whose: "you" }, { view: "graph", alex: false, whose: "you" }]);
});

test("History is your repository beside the mothership, and Crew the mothership over both stations", async () => {
  const run = screen();
  await settle();
  run.click(".pg-tab[data-view=\"history\"]");
  await settle();
  assert.ok(run.q(".pg-picture .viz.is-chart"));
  run.click(".pg-tab[data-view=\"crew\"]");
  await settle();
  assert.ok(run.q(".pg-picture .viz.is-crew"));
});

test("an address naming a view opens on it instead of the remembered one", async () => {
  const run = screen({ route: { picture: "desk" } });
  await settle();
  assert.equal(picked(run), "desk");
});

test("while Alex is shown, a per-person view can draw your repository or Alex's, and saves the choice", async () => {
  const run = screen({ playground: Pg.playground({ prefs: { alex: true } }) });
  await settle();
  const whose = run.q(".pg-whose");
  assert.equal(whose.hidden, false);
  assert.deepEqual([...whose.querySelectorAll("button")].map((button) => button.textContent), ["Your repository", "Alex's repository"]);
  run.click(".pg-whose button[data-whose=\"alex\"]");
  await settle();
  assert.equal(run.q(".pg-picture .chain").dataset.owner, "alex");
  assert.deepEqual(run.calls("/api/playground/prefs").at(-1).body, { view: "chain", alex: true, whose: "alex" });
  run.click(".pg-tab[data-view=\"history\"]");
  await settle();
  assert.ok(run.q(".pg-whose").hidden, "History shows both people");
});

test("with Alex hidden there is no choice of whose repository", async () => {
  const run = screen();
  await settle();
  assert.ok(run.q(".pg-whose").hidden);
});

test("the Conflict tab is there while a file has markers, and stays until the merge is committed", async () => {
  let lab = Pg.observation({ you: Pg.person({ markers: [Pg.marked()], project: Pg.snapshot({ operation: "merge" }) }) });
  const run = screen({ playground: Pg.playground({ start: "conflict" }), lab: () => lab });
  await run.clock.advance(0);
  assert.deepEqual(tabs(run).slice(0, 5), ["chain", "history", "desk", "crew", "conflict"]);
  assert.equal(picked(run), "conflict");
  assert.deepEqual(run.q(".pg-tab[data-view=\"conflict\"]").scrolledIntoView, { block: "nearest", inline: "nearest" }, "a phone's row of tabs scrolls to it");
  lab = Pg.observation({ you: Pg.person({ project: Pg.snapshot({ operation: "merge" }) }) });
  await run.clock.advance(1500);
  assert.ok(tabs(run).includes("conflict"));
  lab = Pg.observation();
  await run.clock.advance(1500);
  assert.ok(!tabs(run).includes("conflict"));
  assert.equal(picked(run), "chain");
});

test("the move log stays empty until git reflog is typed, then fills, says once it is live, and the chain shows what only it reaches", async () => {
  const ghost = Pg.commit("g", ["c"]);
  const entry = { old: Pg.hash("g"), new: Pg.hash("c"), message: "checkout: moving from thrusters to main", line: "ccccccc HEAD@{0}: checkout: moving from thrusters to main" };
  let lab = Pg.observation({ you: Pg.person({ reflog: [entry], ghosts: [ghost] }) });
  const run = screen({ playground: Pg.playground({ start: "lost" }), lab: () => lab });
  await run.clock.advance(0);
  assert.equal(picked(run), "movelog");
  assert.equal(run.all(".pg-picture .movelog-row").length, 0);
  assert.equal(run.q(".pg-live"), null);
  lab = Pg.observation({ you: Pg.person({ reflog: [entry], ghosts: [ghost], commands: [{ line: "git reflog", status: 0 }] }) });
  await run.clock.advance(1500);
  assert.equal(run.all(".pg-picture .movelog-row").length, 1);
  assert.match(run.q(".pg-live").textContent, /^Live here/);
  lab = Pg.observation({ you: Pg.person({ reflog: [entry], ghosts: [ghost] }) });
  run.click(".pg-tab[data-view=\"chain\"]");
  await run.clock.advance(1500);
  assert.ok(run.q(`.pg-picture .chain-row[data-hash="${Pg.hash("g")}"]`));
  run.click(".pg-more-button");
  run.click(".pg-tab[data-view=\"movelog\"]");
  await settle();
  assert.equal(run.all(".pg-picture .movelog-row").length, 1);
  assert.equal(run.q(".pg-live"), null, "said once");
});

test("the chain names work in no commit yet under it", async () => {
  const files = [Pg.file("notes.txt", { folder: "x", folder_change: "modified" }), Pg.file("crew.txt")];
  const run = screen({ lab: Pg.observation({ you: Pg.person({ project: Pg.snapshot({ files }) }) }) });
  await run.clock.advance(0);
  assert.equal(run.q(".pg-loose").textContent, "In your folder, in no commit yet: notes.txt (modified)");
});

test("on a phone the picture starts folded into one line saying what it shows, and a tap unfolds it", async () => {
  const run = screen();
  await run.clock.advance(0);
  const fold = run.q(".pg-fold");
  assert.ok(run.q(".pg-pictured").classList.contains("is-folded"));
  assert.equal(fold.getAttribute("aria-expanded"), "false");
  assert.equal(run.q(".pg-fold-line").textContent, PlaygroundSummary.line({ view: "chain", whose: null, project: Pg.observation().you.project }));
  run.click(".pg-fold");
  assert.equal(run.q(".pg-pictured").classList.contains("is-folded"), false);
  assert.equal(fold.getAttribute("aria-expanded"), "true");
});

test("the legend folds behind i", async () => {
  const run = screen();
  await run.clock.advance(0);
  const key = run.q(".pg-key");
  assert.equal(key.textContent, "i");
  assert.equal(key.getAttribute("aria-label"), "What the marks mean");
  assert.equal(key.getAttribute("aria-pressed"), "false");
  assert.equal(run.q(".pg-pictured").classList.contains("is-keyed"), false);
  run.click(".pg-key");
  assert.equal(run.q(".pg-pictured").classList.contains("is-keyed"), true);
  assert.equal(key.getAttribute("aria-pressed"), "true");
});

test("the lab is looked at again and again while the playground is open, and no more once it is left", async () => {
  const run = screen();
  await run.clock.advance(3000);
  const looks = run.calls("/api/playground/observe").length;
  assert.ok(looks >= 3);
  run.view.dispose();
  await run.clock.advance(6000);
  assert.equal(run.calls("/api/playground/observe").length, looks);
});

test("with no start yet, the playground asks where to start, then opens there", async () => {
  const run = screen({ playground: Pg.playground({ start: null }) });
  await settle();
  const choices = run.all(".pg-choice");
  assert.equal(choices.length, 7);
  choices[3].dispatchEvent(makeEvent("click"));
  await settle();
  assert.deepEqual(run.calls("/api/playground/start").map((call) => call.body), [{ start: "alex-ahead" }]);
  assert.equal(run.q(".pg-start").textContent, "Start alex-ahead");
  assert.equal(picked(run), "history");
});

test("your terminal opens in its own frame, named yours, and Alex's stays closed by default", async () => {
  const run = screen();
  await settle();
  const yours = run.q(".pg-term[data-who=\"you\"]");
  assert.equal(yours.querySelector(".pg-term-name").textContent, "Your terminal");
  assert.equal(run.shells.you, yours.querySelector(".pg-term-host"));
  assert.ok(run.q(".pg-term[data-who=\"alex\"]").hidden);
  assert.deepEqual(run.shells.attached, [["you", "s1"]]);
});

test("Show Alex's terminal opens Alex's shell in a frame of its own under yours, and the choice is remembered", async () => {
  const run = screen();
  await settle();
  const toggle = run.q(".pg-alex-toggle");
  assert.equal(toggle.textContent, "Show Alex's terminal");
  run.click(".pg-alex-toggle");
  await settle();
  const alex = run.q(".pg-term[data-who=\"alex\"]");
  assert.equal(alex.hidden, false);
  assert.equal(alex.querySelector(".pg-term-name").textContent, "Alex's terminal");
  assert.deepEqual(run.shells.attached, [["you", "s1"], ["alex", "s1"]]);
  assert.equal(toggle.textContent, "Hide Alex's terminal");
  assert.deepEqual(run.calls("/api/playground/prefs").at(-1).body, { view: "chain", alex: true, whose: "you" });
  run.click(".pg-alex-toggle");
  await settle();
  assert.ok(alex.hidden);
  assert.equal(toggle.textContent, "Show Alex's terminal");
  assert.deepEqual(run.calls("/api/playground/prefs").at(-1).body, { view: "chain", alex: false, whose: "you" });
  assert.equal(run.shells.attached.length, 2, "Alex's shell is kept, only hidden");
});

test("a start about two people opens with Alex's terminal shown", async () => {
  const run = screen({ playground: Pg.playground({ start: "alex-ahead" }) });
  await settle();
  assert.equal(run.q(".pg-term[data-who=\"alex\"]").hidden, false);
  assert.deepEqual(run.shells.attached.map(([person]) => person), ["you", "alex"]);
});

test("with no mothership there is no Alex and no toggle for Alex", async () => {
  const run = screen({ playground: Pg.playground({ start: "empty" }), lab: Pg.observation({ start: "empty", alex: null, github: null }) });
  await settle();
  assert.equal(run.q(".pg-alex-toggle"), null);
  assert.ok(run.q(".pg-term[data-who=\"alex\"]").hidden);
});

test("on a phone one switch picks the terminal shown, and the picture follows it", async () => {
  const run = screen({ playground: Pg.playground({ start: "alex-ahead", prefs: { view: "chain" } }) });
  await run.clock.advance(0);
  const terms = run.q(".pg-terms");
  assert.equal(run.q(".pg-termswitch").hidden, false);
  assert.deepEqual(run.all(".pg-termswitch button").map((button) => button.textContent), ["You", "Alex"]);
  assert.equal(terms.dataset.whose, "you");
  run.click(".pg-termswitch button[data-whose=\"alex\"]");
  await settle();
  assert.equal(terms.dataset.whose, "alex");
  assert.equal(run.q(".pg-picture .chain").dataset.owner, "alex");
  assert.equal(run.q(".pg-termswitch button[data-whose=\"alex\"]").getAttribute("aria-pressed"), "true");
  assert.deepEqual(run.calls("/api/playground/prefs").at(-1).body, { view: "chain", alex: true, whose: "alex" });
});

test("with Alex hidden the phone has no terminal switch", async () => {
  const run = screen();
  await run.clock.advance(0);
  assert.ok(run.q(".pg-termswitch").hidden);
});

test("leaving the playground takes its terminals off the page without closing them", async () => {
  const run = screen();
  await settle();
  run.view.dispose();
  assert.equal(run.shells.detached, 1);
});

test("the Conflict view is click to keep: Write goes to the server for your repository and the lab is looked at again at once", async () => {
  const lab = Pg.observation({ you: Pg.person({ markers: [Pg.marked()], project: Pg.snapshot({ operation: "merge" }) }) });
  const run = screen({ playground: Pg.playground({ start: "conflict" }), lab });
  await run.clock.advance(0);
  assert.ok(run.q(".pg-picture .keep"));
  const looks = run.calls("/api/playground/observe").length;
  run.click(".keep-pick[data-choice=\"yours\"]");
  run.click(".keep-write");
  await settle();
  await settle();
  assert.deepEqual(run.calls("/api/playground/resolve").map((call) => call.body), [{ person: "you", file: "checklist.txt", read: "r1", choices: ["yours"] }]);
  assert.equal(run.calls("/api/playground/observe").length, looks + 1);
});

test("the panel's editor chips type their command in the terminal of the repository it shows", async () => {
  const lab = Pg.observation({ you: Pg.person({ markers: [Pg.marked()] }), alex: Pg.person({ markers: [Pg.marked()] }) });
  const run = screen({ playground: Pg.playground({ start: "conflict", prefs: { whose: "alex" } }), lab });
  await run.clock.advance(0);
  run.click(".keep-chip[data-editor=\"nano\"]");
  assert.deepEqual(run.shells.typed, [["alex", "nano checklist.txt"]]);
});

test("an editor in a terminal shows its strip above that terminal, and the conflict panel waits for it", async () => {
  const lab = Pg.observation({ you: Pg.person({ markers: [Pg.marked()] }) });
  const run = screen({ playground: Pg.playground({ start: "conflict" }), lab });
  await run.clock.advance(0);
  const strip = run.q(".pg-term[data-who=\"you\"] .pg-strip");
  assert.ok(strip.hidden);
  run.shells.titles.you("editor vim checklist.txt");
  assert.equal(strip.hidden, false);
  assert.equal(strip.dataset.editor, "vim");
  assert.ok(run.q(".pg-term[data-who=\"alex\"] .pg-strip").hidden);
  assert.ok(run.q(".keep").classList.contains("is-waiting"));
  run.shells.titles.you("");
  assert.ok(strip.hidden);
  assert.equal(run.q(".keep").classList.contains("is-waiting"), false);
});

test("Get me out types the editor's quit keys in its own terminal", async () => {
  const run = screen({ playground: Pg.playground({ start: "alex-ahead" }) });
  await run.clock.advance(0);
  run.shells.titles.alex("editor vim notes.txt insert");
  run.q(".pg-term[data-who=\"alex\"] .pg-strip-out").dispatchEvent(makeEvent("click"));
  await settle();
  document.body.querySelector("dialog button.is-confirm").dispatchEvent(makeEvent("click"));
  await settle();
  assert.deepEqual(run.shells.keys, [["alex", "\x1b:q!\r"]]);
});
