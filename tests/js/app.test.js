"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { fakeServer, httpError, installBrowser, load, record, settle } = require("./load");

installBrowser();
const { Dom } = load(
  ["dom.js", "markup.js", "map.js", "api.js", "progress.js", "route.js", "poll.js", "sound.js", "dialog.js", "celebrate.js", "live.js", "lesson.js", "quest.js", "challenge.js", "practice.js", "level.js", "cards.js", "notes.js", "home.js"],
  ["Dom"],
);

/* A fresh page with index.html's header, the given address, key and server; then app.js boots. */
async function boot({ hash = "#/", token = "KEY", replies = {}, stored = {}, wrap = (api) => api } = {}) {
  const document = installBrowser();
  const { el } = Dom;
  document.body.append(
    el("header", { class: "topbar" },
      el("nav", { class: "nav" }, el("a", { href: "#/", "data-view": "home" }, "Map"), el("a", { href: "#/cards", "data-view": "cards" }, "Cards", el("span", { class: "badge", hidden: true })), el("a", { href: "#/notes", "data-view": "notes" }, "Notes")),
      el("div", { class: "player", hidden: true }, el("span", { class: "player-rank" }), el("span", { class: "meter small" }, el("i")), el("span", { class: "player-xp" })),
      el("button", { class: "pref pref-theme" }), el("button", { class: "pref pref-sound" }),
    ),
    el("main", { id: "app" }),
    el("div", { class: "toasts" }),
  );
  const storage = new Map(Object.entries(stored));
  const windowListeners = new Map();
  const server = fakeServer({ "/api/status": { ...record("status"), active: null }, "/api/cards": { cards: record("cards") }, "/api/notes": record("notes"), ...replies });
  const seen = { locked: 0, terminals: 0 };
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
    createTerminal: () => {
      seen.terminals += 1;
      return { element: el("div", { class: "term-dock" }), start() {}, setLook() {}, type() {}, dispose() {} };
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

test("with a key the map shows, and the header shows the rank, the XP and the cards due", async () => {
  const page = await boot();
  assert.ok(page.main.querySelector(".home"));
  assert.equal(page.document.querySelector(".player").hidden, false);
  assert.equal(page.document.querySelector(".player-rank").textContent, "Committer");
  assert.equal(page.document.querySelector(".player-xp").textContent, "260 XP");
  assert.equal(page.document.querySelector(".nav .badge").textContent, "4");
  assert.ok(page.document.querySelector(".nav a[data-view=\"home\"]").hasAttribute("aria-current"));
});

test("the address in the link that carried the key is opened", async () => {
  const page = await boot({ hash: "#/notes/basics&token=KEY" });
  assert.equal(global.location.hash, "#/notes/basics");
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
  const toasts = page.document.querySelectorAll(".toast").map((toast) => toast.textContent);
  assert.match(toasts[0], /bad reply/);
  assert.match(toasts[1], /did not answer/);
});

test("a server that does not answer at the start says how to start it again", async () => {
  const page = await boot({ replies: { "/api/status": httpError(0, "no answer") } });
  assert.match(page.main.textContent, /Cannot reach the game/);
});

test("a damaged save is named, and starting over resets it after asking", async () => {
  let damaged = true;
  const status = () => (damaged ? httpError(500, "progress.json: xp should be a number") : { ...record("status"), active: null });
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
  assert.ok(page.main.querySelector(".home"));
});

test("a damaged save met during play is named in a message", async () => {
  const page = await boot();
  page.fire("unhandledrejection", { reason: httpError(500, "active.json: step should be a number") });
  assert.match(page.document.querySelector(".toast").textContent, /saved game is damaged.*active\.json/);
});
