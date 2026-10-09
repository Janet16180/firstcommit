"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { fakeServer, httpError, installBrowser, load, record, settle } = require("./load");

const document = installBrowser();
const { NotesView, createGameApi } = load(["dom.js", "strings.js", "markup.js", "api.js", "progress.js", "notes.js"], ["NotesView", "createGameApi"]);

function notes(chapter, { status = record("status"), reply = record("notes") } = {}) {
  const server = fakeServer({ "/api/notes": reply });
  const view = NotesView.create({ game: createGameApi(server.api), status: () => status }, chapter);
  document.body.replaceChildren(view.element);
  return { view, server, q: (selector) => view.element.querySelector(selector) };
}

test("a chapter's notes are shown with its title", async () => {
  const run = notes("cargo");
  await settle();
  assert.equal(run.server.calls[0].path, "/api/notes?chapter=cargo");
  assert.equal(run.q("article h1").textContent, "The cargo dock");
  assert.match(run.q("article").textContent, /git add: stage a file/);
});

test("every chapter is listed, the open one marked, and one with no levels is coming soon, not a link", async () => {
  const run = notes("cargo");
  await settle();
  const items = run.q("nav").querySelectorAll("li");
  assert.equal(items.length, 3);
  assert.deepEqual([...run.q("nav").querySelectorAll("a")].map((link) => link.getAttribute("href")), ["#/notes/cargo"]);
  assert.match(items[0].textContent, /Git, GitHub and your first clone.*Coming soon/);
  assert.equal(run.q("nav a[aria-current=\"page\"]").getAttribute("href"), "#/notes/cargo");
});

test("without a chapter, the one of the level in progress opens", async () => {
  const run = notes(null);
  await settle();
  assert.equal(run.server.calls[0].path, "/api/notes?chapter=cargo");
});

test("without a chapter or a level in progress, the first chapter with cards opens", async () => {
  const run = notes(null, { status: { ...record("status"), active: null } });
  await settle();
  assert.equal(run.server.calls[0].path, "/api/notes?chapter=cargo");
});

test("a chapter without notes says so", async () => {
  const run = notes("vault", { reply: httpError(404, "unknown id") });
  await settle();
  assert.match(run.q("article").textContent, /No notes for this chapter yet/);
});
