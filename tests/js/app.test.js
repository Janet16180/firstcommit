"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { fakeServer, httpError, installBrowser, load, record, settle } = require("./load");

installBrowser();
const { Dom } = load(
  ["dom.js", "strings.js", "places.js", "markup.js", "art-pixels.js", "art-sprites.js", "art-sky.js", "art-scenes.js", "art-moments.js", "api.js", "progress.js", "route.js", "poll.js", "sound.js", "dialog.js", "typed.js", "zones.js", "zone-panel.js", "mission.js", "comms.js", "completion.js", "scene.js", "moment-layer.js", "view-tabs.js", "strip.js", "sides.js", "tape.js", "births.js", "chain.js", "folder-row.js", "desk.js", "move-log.js", "target-chart.js", "git-graph.js", "pictures.js", "level-screen.js", "starmap.js", "art-infographics.js", "infographic-text.js", "guide-git.js", "guide-text.js", "guide-pictures.js", "guide-card.js", "guide-conflict.js", "field-guide.js", "cards.js", "notes.js", "dev.js", "playground-summary.js", "keep-panel.js", "merge-tool.js", "editor-strip.js", "playground-picture.js", "playground-screen.js"],
  ["Dom"],
);

/* A fresh page with index.html's header, the given address, key and server; then app.js boots. */
async function boot({ hash = "#/", token = "KEY", replies = {}, stored = {}, wrap = (api) => api, browserLanguage = "en-US" } = {}) {
  const document = installBrowser();
  const { el } = Dom;
  document.body.append(
    el("header", { class: "topbar" },
      el("nav", { class: "nav" }, el("a", { href: "#/", "data-view": "home", "data-text": "nav.map" }, "Map"), el("a", { href: "#/cards", "data-view": "cards" }, el("span", { "data-text": "nav.cards" }, "Cards"), el("span", { class: "badge", hidden: true })), el("a", { href: "#/notes", "data-view": "notes", "data-text": "nav.notes" }, "Notes")),
      el("div", { class: "player", hidden: true }, el("span", { class: "player-rank" }), el("span", { class: "meter small" }, el("i")), el("span", { class: "player-xp" })),
      el("button", { class: "pref pref-theme" }), el("button", { class: "pref pref-sound" }), el("button", { class: "pref pref-language" }),
    ),
    el("main", { id: "app" }),
    el("div", { class: "toasts" }),
  );
  const storage = new Map(Object.entries(stored));
  const windowListeners = new Map();
  const server = fakeServer({ "/api/status": { ...record("status"), active: null }, "/api/cards": { cards: record("cards") }, "/api/notes": record("notes"), ...replies });
  const seen = { locked: 0, terminals: 0, runs: [] };
  Object.defineProperty(global, "navigator", { value: { language: browserLanguage }, configurable: true });
  Object.assign(global, {
    location: { hash, pathname: "/", search: "" },
    history: { replaceState: (state, title, address) => (global.location.hash = address.startsWith("#") ? address : "") },
    localStorage: { getItem: (key) => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value), removeItem: (key) => storage.delete(key) },
    addEventListener: (type, listener) => windowListeners.set(type, [...(windowListeners.get(type) || []), listener]),
    scrollTo: () => {},
    createClient: (options) => {
      if (global.location.hash.includes("token=")) global.location.hash = "";
      return { token: () => token, api: wrap(server.api), options };
    },
    createTerminal: (options) => {
      seen.terminals += 1;
      seen.paths = [...(seen.paths || []), options.path];
      seen.onTitle = [...(seen.onTitle || []), options.onTitle];
      seen.onClose = [...(seen.onClose || []), options.onClose];
      seen.looks = options.looks;
      seen.labels = [options.labels];
      return { element: el("div", { class: "term-dock" }), start() {}, setLook() {}, setLabels: (labels) => seen.labels.push(labels), type() {}, run: (line) => seen.runs.push(line), keys: (raw) => (seen.keys = [...(seen.keys || []), raw]), dispose: () => (seen.disposed = (seen.disposed || 0) + 1) };
    },
  });
  load(["app.js"], []);
  await settle();
  await settle();
  const fire = (type, event) => (windowListeners.get(type) || []).forEach((listener) => listener(event));
  return { document, server, storage, seen, fire, main: document.getElementById("app") };
}

test("without an access key the page asks for the link and calls no route", async () => {
  const page = await boot({ token: null });
  assert.match(page.main.textContent, /link that firstcommit printed/);
  assert.equal(page.server.calls.length, 0);
});

/* Opens the sample level, in progress, runs `check(page)`, then leaves for the map so its polling
   stops. The level keeps today's views unless `level` says otherwise. */
async function onLevel(check, level = { ...record("level"), pictures: null }) {
  const active = record("active");
  const page = await boot({
    hash: `#/level/${active.level}`,
    replies: { "/api/status": { ...record("status"), active }, "/api/level": level, "/api/view": {}, "/api/observe": record("observation"), "/api/step": record("step"), "/api/check": record("check_unsolved") },
  });
  try {
    await settle();
    await check(page);
  } finally {
    global.location.hash = "#/";
    page.fire("hashchange", {});
    await settle();
  }
}

test("in dev mode the level's Solve button runs the solution's lines in the page's terminal", async () => {
  const active = record("active");
  const page = await boot({
    hash: `#/level/${active.level}`,
    replies: { "/api/status": { ...record("status"), active, dev: true }, "/api/level": { ...record("level"), pictures: null }, "/api/view": {}, "/api/observe": record("observation"), "/api/step": record("step"), "/api/check": record("check_unsolved") },
  });
  try {
    await settle();
    page.main.querySelector(".hud .solve").click();
    await settle();
    await settle();
    assert.deepEqual(page.seen.runs, [record("level").solution.lines[0]]);
  } finally {
    global.location.hash = "#/";
    page.fire("hashchange", {});
    await settle();
  }
});

test("a level's address opens the level screen, with its zones and the terminal under Rama's line", () => onLevel((page) => {
  assert.ok(page.main.querySelector(".level-screen .viz"));
  assert.equal(page.seen.terminals, 1);
  assert.ok(page.main.querySelector(".termcol .term-dock"));
}));

test("a level with teaching pictures opens on its chain, drawn from the lab, with the terminal under Rama's line", () => onLevel(async (page) => {
  await settle();
  await settle();
  const chain = page.main.querySelector(".level-screen .sky .pictures .chain");
  assert.equal(chain.querySelectorAll(".chain-row").length, record("observation").project.commits.length);
  assert.ok(page.main.querySelector(".termcol .term-dock"));
}, { ...record("level"), scene_seen: true }));

test("the terminal wears the design's night colours and VT323 at the design's size, in both looks", () => onLevel((page) => {
  assert.equal(page.seen.looks.light.theme.background, "#120F2C");
  assert.match(page.seen.looks.light.fontFamily, /^VT323, /);
  assert.equal(page.seen.looks.light.fontSize, 19);
  assert.deepEqual(page.seen.looks.dark.theme, page.seen.looks.light.theme);
}));

test("the map and the level screen have their own heads; the header bar shows over the cards and the notes", async () => {
  const page = await boot();
  assert.equal(page.document.querySelector(".topbar").hidden, true);
  global.location.hash = "#/cards";
  page.fire("hashchange", makeEvent("hashchange"));
  await settle();
  await settle();
  assert.equal(page.document.querySelector(".topbar").hidden, false);
});

test("the space dust lies behind every view", async () => {
  const page = await boot();
  assert.ok(page.document.body.querySelector("svg.art-dust"));
});

test("the map's bar has its own look and sound buttons, which change the look like the header's", async () => {
  const page = await boot({ stored: { "firstcommit.theme": "light" } });
  const button = page.main.querySelector(".map-bar .pref-theme");
  assert.equal(button.textContent, "Look: light");
  button.click();
  assert.equal(page.document.documentElement.dataset.theme, "dark");
  assert.equal(page.main.querySelector(".map-bar .pref-theme").textContent, "Look: dark");
  assert.equal(page.document.querySelector(".topbar .pref-theme").textContent, "Look: dark");
  const sound = page.main.querySelector(".map-bar .pref-sound");
  const before = sound.textContent;
  sound.click();
  assert.notEqual(sound.textContent, before);
});

test("with a key the map shows, and the header keeps the rank, the XP and the cards due", async () => {
  const page = await boot();
  assert.ok(page.main.querySelector(".starmap"));
  assert.equal(page.document.querySelector(".player").hidden, false);
  assert.equal(page.document.querySelector(".player-rank").textContent, "Committer");
  assert.equal(page.document.querySelector(".player-xp").textContent, "260 XP");
  assert.equal(page.document.querySelector(".nav .badge").textContent, "4");
  assert.ok(page.document.querySelector(".nav a[data-view=\"home\"]").hasAttribute("aria-current"));
});

test("the address in the link that carried the key is opened", async () => {
  const page = await boot({ hash: "#/notes/cargo&token=KEY" });
  assert.equal(global.location.hash, "#/notes/cargo");
  assert.ok(page.main.querySelector(".notes-page"));
});

test("changing the address shows its view and marks it in the menu", async () => {
  const page = await boot();
  global.location.hash = "#/cards";
  page.fire("hashchange", makeEvent("hashchange"));
  await settle();
  await settle();
  assert.ok(page.main.querySelector(".cards"));
  assert.ok(page.document.querySelector(".nav a[data-view=\"cards\"]").hasAttribute("aria-current"));
});

test("a newer navigation wins over a slower one that started before it", async () => {
  const held = [];
  let hold = false;
  const wrap = (api) => (target, body) => (hold && target === "/api/status" ? new Promise((resolve) => held.push(() => resolve(api(target, body)))) : api(target, body));
  const page = await boot({ wrap });
  hold = true;
  global.location.hash = "#/cards";
  page.fire("hashchange", makeEvent("hashchange"));
  hold = false;
  global.location.hash = "#/notes";
  page.fire("hashchange", makeEvent("hashchange"));
  await settle();
  await settle();
  assert.ok(page.main.querySelector(".notes-page"));
  held.forEach((release) => release());
  await settle();
  await settle();
  assert.ok(page.main.querySelector(".notes-page"));
  assert.equal(page.main.querySelector(".cards"), null);
});

test("the look follows the system until the player picks light or dark, and the choice is kept", async () => {
  const page = await boot({ stored: { "firstcommit.theme": "dark" } });
  assert.equal(page.document.documentElement.dataset.theme, "dark");
  const button = page.document.querySelector(".pref-theme");
  button.click();
  assert.equal(page.storage.get("firstcommit.theme"), "auto");
  assert.equal(page.document.documentElement.dataset.theme, "light");
  button.click();
  assert.equal(page.storage.get("firstcommit.theme"), "light");
});

test("Shift+Tab in the terminal is kept from the shell so focus can leave, and Tab still completes", async () => {
  const page = await boot();
  const host = page.document.createElement("div");
  host.className = "term-host";
  page.document.body.append(host);
  const shiftTab = makeEvent("keydown", { key: "Tab", shiftKey: true, target: host });
  const tab = makeEvent("keydown", { key: "Tab", shiftKey: false, target: host });
  page.document.dispatchEvent(shiftTab);
  page.document.dispatchEvent(tab);
  assert.equal(shiftTab.stopped, true);
  assert.equal(tab.stopped, false);
  assert.equal(shiftTab.defaultPrevented, false);
});

test("an error no view handled is shown, and a server that does not answer is named", async () => {
  const page = await boot();
  page.fire("unhandledrejection", { reason: new Error("bad reply") });
  page.fire("unhandledrejection", { reason: httpError(0, "no answer") });
  const toasts = [...page.document.querySelectorAll(".toast")].map((toast) => toast.textContent);
  assert.match(toasts[0], /bad reply/);
  assert.match(toasts[1], /did not answer/);
});

test("a server that does not answer at the start says how to start it again", async () => {
  const page = await boot({ replies: { "/api/status": httpError(0, "no answer") } });
  assert.match(page.main.textContent, /Cannot reach the game/);
});

test("a damaged save is named, and starting over resets it after asking", async () => {
  let damaged = true;
  const status = () => (damaged ? httpError(500, "progress.json: xp should be a number", { kind: "save" }) : { ...record("status"), active: null });
  const reset = () => {
    damaged = false;
    return {};
  };
  const page = await boot({ replies: { "/api/status": status, "/api/reset": reset } });
  assert.match(page.main.textContent, /saved game is damaged.*progress\.json: xp should be a number/);
  page.main.querySelector("button.start-over").click();
  page.document.body.querySelector("dialog button.is-confirm").click();
  await settle();
  await settle();
  assert.equal(page.server.calls.filter((call) => call.path === "/api/reset").length, 1);
  assert.ok(page.main.querySelector(".starmap"));
});

test("a damaged save met during play is named in a message", async () => {
  const page = await boot();
  page.fire("unhandledrejection", { reason: httpError(500, "active.json: step should be a number", { kind: "save" }) });
  assert.match(page.document.querySelector(".toast").textContent, /saved game is damaged.*active\.json/);
});

const bug = () => httpError(500, "IndexError: tuple index out of range", { error: "IndexError: tuple index out of range", kind: "bug" });

test("a bug met at the start is named as a bug, points to the server's terminal and offers no start over", async () => {
  const page = await boot({ replies: { "/api/status": bug() } });
  assert.match(page.main.textContent, /The game hit a bug/);
  assert.match(page.main.textContent, /IndexError: tuple index out of range/);
  assert.match(page.main.textContent, /terminal where firstcommit is running/);
  assert.doesNotMatch(page.main.textContent, /damaged|did not answer|Cannot reach/);
  assert.equal(page.main.querySelector("button.start-over"), null);
});

test("a bug met during play is named as a bug, not as a damaged save or a stopped server", async () => {
  const page = await boot();
  page.fire("unhandledrejection", { reason: bug() });
  const toast = page.document.querySelector(".toast").textContent;
  assert.match(toast, /The game hit a bug: IndexError/);
  assert.match(toast, /terminal where firstcommit is running/);
  assert.doesNotMatch(toast, /damaged|did not answer/);
});

test("a 500 that does not say its kind is never taken for a damaged save", async () => {
  const page = await boot({ replies: { "/api/status": httpError(500, "500 Internal Server Error") } });
  assert.equal(page.main.querySelector("button.start-over"), null);
  assert.match(page.main.textContent, /The game hit a bug/);
});

test("the field guide's address shows the guide under its own head", async () => {
  const page = await boot({ hash: "#/guide" });
  assert.ok(page.main.querySelector(".field-guide"));
  assert.equal(page.document.querySelector(".topbar").hidden, true);
});

test("dev mode's address lists every level, under the page's top bar", async () => {
  const page = await boot({ hash: "#/dev", replies: { "/api/status": { ...record("status"), dev: true }, "/api/playground": require("./playground-records").playground() } });
  assert.ok(page.main.querySelector(".dev .dev-level a"));
  assert.equal(page.document.querySelector(".topbar").hidden, false);
  assert.match(page.document.title, /^Dev mode/);
});

test("before the game answers, the page speaks English, whatever the browser's language", async () => {
  const page = await boot({ token: null, browserLanguage: "es-MX" });
  assert.equal(page.document.documentElement.lang, "en");
  assert.match(page.main.querySelector("h1").textContent, /link/);
});

test("once the game answers, the page speaks the game's language, whatever the browser's", async () => {
  const page = await boot({ browserLanguage: "en-US", replies: { "/api/status": { ...record("status"), active: null, language: "es" } } });
  assert.equal(page.document.documentElement.lang, "es");
  assert.equal(page.document.querySelector(".nav a").textContent, "Mapa");
  assert.equal(page.main.querySelector(".map-bar .pref-language").textContent, "English");
});

test("the map bar's language button tells the game, then reloads the records in the new language", async () => {
  let language = "en";
  const page = await boot({
    replies: {
      "/api/status": () => ({ ...record("status"), active: null, language }),
      "/api/language": (body) => {
        language = body.language;
        return {};
      },
    },
  });
  page.main.querySelector(".map-bar .pref-language").click();
  await settle();
  await settle();
  const paths = page.server.calls.map((call) => call.path);
  const told = paths.indexOf("/api/language");
  assert.deepEqual(page.server.calls[told].body, { language: "es" });
  assert.ok(paths.lastIndexOf("/api/status") > told);
  assert.equal(page.document.documentElement.lang, "es");
  assert.equal(page.document.querySelector(".nav a").textContent, "Mapa");
  assert.equal(page.document.querySelector(".topbar .pref-language").textContent, "English");
  assert.equal(page.main.querySelector(".map-bar .pref-language").textContent, "English");
  assert.equal(page.storage.size, 0);
});

test("the terminal's status and button speak the game's language, and follow a switch", async () => {
  let language = "es";
  const active = record("active");
  const page = await boot({
    hash: `#/level/${active.level}`,
    replies: {
      "/api/status": () => ({ ...record("status"), active, language }),
      "/api/language": (body) => {
        language = body.language;
        return {};
      },
      "/api/level": { ...record("level"), pictures: null },
      "/api/view": {},
      "/api/observe": record("observation"),
      "/api/step": record("step"),
      "/api/check": record("check_unsolved"),
    },
  });
  await settle();
  try {
    assert.deepEqual(page.seen.labels[0], { connecting: "conectando", connected: "conectado", hide: "ocultar", show: "mostrar", hint: "Ctrl+V pega · Ctrl+C copia lo seleccionado" });
  } finally {
    global.location.hash = "#/";
    page.fire("hashchange", {});
    await settle();
  }
  page.main.querySelector(".map-bar .pref-language").click();
  await settle();
  await settle();
  assert.deepEqual(page.seen.labels.at(-1), { connecting: "connecting", connected: "connected", hide: "hide", show: "show", hint: "Ctrl+V paste · Ctrl+C copies a selection" });
});

const Pg = require("./playground-records");

test("the playground's address opens it under its own head, with its two shells on their own endpoints, kept while its start stands", async () => {
  let built = Pg.playground({ start: "alex-ahead" });
  const page = await boot({ hash: "#/playground", replies: { "/api/playground": () => built, "/api/playground/observe": () => Pg.observation({ started: built.current.started }), "/api/playground/prefs": () => Pg.playground() } });
  const go = async (hash) => {
    global.location.hash = hash;
    page.fire("hashchange", {});
    await settle();
    await settle();
  };
  try {
    assert.ok(page.main.querySelector(".pg"));
    assert.ok(page.document.querySelector(".topbar").hidden);
    assert.deepEqual(page.seen.paths, ["/api/terminal/playground", "/api/terminal/playground-alex"]);
    await go("#/");
    await go("#/playground");
    assert.equal(page.seen.terminals, 2, "the same shells, put back");
    assert.equal(page.seen.disposed || 0, 0);
    built = Pg.playground({ start: "alex-ahead", started: "s2" });
    await go("#/");
    await go("#/playground");
    assert.equal(page.seen.terminals, 4);
    assert.equal(page.seen.disposed, 2, "a start built again gets new shells");
  } finally {
    await go("#/");
  }
});

test("a playground shell's title reaches the playground, even one set while the player was away", async () => {
  const built = Pg.playground({ start: "branches" });
  const page = await boot({ hash: "#/playground", replies: { "/api/playground": built, "/api/playground/observe": Pg.observation(), "/api/playground/prefs": () => Pg.playground() } });
  const go = async (hash) => {
    global.location.hash = hash;
    page.fire("hashchange", {});
    await settle();
    await settle();
  };
  const strip = () => page.main.querySelector(".pg-term[data-who=\"you\"] .pg-strip");
  try {
    page.seen.onTitle[0]("firstcommit-editor nano notes.txt");
    assert.equal(strip().hidden, false);
    await go("#/");
    page.seen.onTitle[0]("");
    page.seen.onTitle[0]("firstcommit-editor vim notes.txt");
    await go("#/playground");
    assert.equal(strip().dataset.editor, "vim");
  } finally {
    await go("#/");
  }
});

test("the playground opened from a mission leads back to it; opened from the map it does not", async () => {
  const active = record("active");
  const page = await boot({
    hash: `#/level/${active.level}`,
    replies: { "/api/status": { ...record("status"), active }, "/api/level": { ...record("level"), pictures: null }, "/api/view": {}, "/api/observe": record("observation"), "/api/playground": Pg.playground(), "/api/playground/observe": Pg.observation(), "/api/playground/prefs": () => Pg.playground() },
  });
  const go = async (hash) => {
    global.location.hash = hash;
    page.fire("hashchange", {});
    await settle();
    await settle();
  };
  try {
    await go("#/playground?start=branches&try=git%20status");
    assert.equal(page.main.querySelector(".pg-back").getAttribute("href"), `#/level/${active.level}`);
    await go("#/");
    await go("#/playground");
    assert.equal(page.main.querySelector(".pg-back"), null);
  } finally {
    await go("#/");
  }
});


test("the level's shell tells the level screen its titles and its closing: the merge tool's panel opens and closes with them", async () => {
  await onLevel(async (page) => {
    const panel = () => page.main.querySelector(".termcol .mtool");
    assert.equal(panel().hidden, true);
    page.seen.onTitle[0]("firstcommit-mergetool launch.txt");
    assert.equal(panel().hidden, false);
    panel().querySelector(".mtool-cancel").click();
    assert.deepEqual(page.seen.keys, ["\x03"]);
    page.seen.onClose[0]();
    assert.equal(panel().hidden, true);
  });
});
