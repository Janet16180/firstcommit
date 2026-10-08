"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { fakeServer, installBrowser, load, record, settle } = require("./load");
const Pg = require("./playground-records");

const document = installBrowser();
const { DevList, Strings, createGameApi } = load(["dom.js", "strings.js", "api.js", "progress.js", "dev.js"], ["DevList", "Strings", "createGameApi"]);

function list(status) {
  const server = fakeServer({ "/api/playground": Pg.playground() });
  const view = DevList.create({ status: () => status, game: createGameApi(server.api) });
  document.body.replaceChildren(view.element);
  return { view, all: (selector) => [...view.element.querySelectorAll(selector)], q: (selector) => view.element.querySelector(selector) };
}

const dev = () => ({ ...record("status"), dev: true });

test("in dev mode every sector is listed with its levels: number, title, id and a link straight to the level", () => {
  const status = dev();
  const run = list(status);
  const withLevels = status.chapters.filter((chapter) => chapter.levels.length);
  assert.deepEqual(run.all(".dev-sector h2").map((node) => node.textContent), status.chapters.map((chapter) => chapter.title));
  const links = run.all(".dev-level a");
  assert.equal(links.length, withLevels.flatMap((chapter) => chapter.levels).length);
  const first = withLevels[0].levels[0];
  assert.equal(links[0].getAttribute("href"), `#/level/${encodeURIComponent(first.id)}`);
  assert.match(links[0].textContent, new RegExp(first.title));
  assert.equal(run.q(".dev-level code").textContent, first.id);
  assert.match(run.q(".dev-level .dev-num").textContent, /\d+\.\d+/);
});

test("a sector with no levels yet says so", () => {
  const status = dev();
  const run = list(status);
  const empty = status.chapters.findIndex((chapter) => !chapter.levels.length);
  assert.ok(empty >= 0);
  assert.equal(run.all(".dev-sector")[empty].querySelector(".dev-none").textContent, "No levels yet.");
});

test("out of dev mode the list stays hidden and says how to turn dev mode on", () => {
  const run = list({ ...record("status"), dev: false });
  assert.equal(run.all(".dev-level").length, 0);
  assert.match(run.view.element.textContent, /firstcommit serve --dev/);
});

test("the list speaks the page's language", () => {
  Strings.use("es");
  try {
    const run = list({ ...record("status"), dev: false });
    assert.match(run.q("h1").textContent, /Modo de desarrollo/);
  } finally {
    Strings.use("en");
  }
});

test("in dev mode a Playground section links to each starting point", async () => {
  const run = list(dev());
  await settle();
  const links = run.all(".dev-playground a");
  assert.equal(run.q(".dev-playground h2").textContent, "Playground");
  assert.deepEqual(links.map((link) => link.getAttribute("href")), Pg.START_IDS.map((id) => `#/playground?start=${id}`));
  assert.match(links[0].textContent, /Empty folder/);
});

test("out of dev mode there is no Playground section", async () => {
  const run = list({ ...record("status"), dev: false });
  await settle();
  assert.equal(run.q(".dev-playground"), null);
});
