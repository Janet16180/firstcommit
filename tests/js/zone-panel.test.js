"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

installBrowser();
const { ZonePanel } = load(["dom.js", "art-pixels.js", "art-sprites.js", "zones.js", "zone-panel.js"], ["ZonePanel"]);

const observe = (project, github = null) => ({ ...record("observation"), project, github });
const zone = (panel, name) => panel.element.querySelector(`.zone[data-zone="${name}"]`);
const texts = (node, selector) => [...node.querySelectorAll(selector)].map((item) => item.textContent);

test("the four zones are named in the design's order, with the git name under each", () => {
  const panel = ZonePanel.create();
  assert.deepEqual(texts(panel.element, ".z-head h3"), ["Workshop", "Cargo dock", "Vault", "Mothership"]);
  assert.deepEqual(texts(panel.element, ".z-head small"), ["working folder", "staging area", "local repository", "remote repository"]);
  assert.equal(panel.element.getAttribute("aria-label"), "Your repository");
});

test("drawn arrows between the zones name the commands that move work along", () => {
  const panel = ZonePanel.create();
  assert.deepEqual(texts(panel.element, ".fl span"), ["git add", "git commit", "git push", "git pull"]);
  assert.equal(panel.element.querySelectorAll(".fl svg.art-icon").length, 4);
  assert.ok(panel.element.querySelector(".fl.is-back"));
});

test("a folder without a repository lights only the workshop, and the other zones say why they are off", () => {
  const panel = ZonePanel.create();
  panel.update(observe(record("snapshots").folder));
  assert.equal(zone(panel, "workshop").classList.contains("is-dormant"), false);
  for (const name of ["dock", "vault", "remote"]) assert.ok(zone(panel, name).classList.contains("is-dormant"), name);
  assert.match(zone(panel, "dock").textContent, /git init/);
  assert.deepEqual(texts(zone(panel, "workshop"), ".fname"), ["notes.txt"]);
  assert.equal(zone(panel, "workshop").querySelector(".file").dataset.state, "none");
  assert.equal(zone(panel, "workshop").querySelector(".z-count").textContent, "1");
  assert.equal(zone(panel, "dock").querySelector(".z-count").textContent, "–");
});

test("files show their state with a tag, and staged changes sit on the dock", () => {
  const panel = ZonePanel.create();
  panel.update(observe({ ...record("snapshots").one, files: record("files") }));
  const workshop = zone(panel, "workshop");
  const newFile = [...workshop.querySelectorAll(".file")].find((item) => item.textContent.startsWith("new.txt"));
  assert.equal(newFile.dataset.state, "new");
  assert.equal(newFile.querySelector(".ftag").textContent, "new");
  assert.deepEqual(texts(zone(panel, "dock"), ".fname"), ["added.txt", "staged.txt", "removed.txt", "staged-link"]);
  assert.equal(zone(panel, "dock").querySelector(".z-count").textContent, "4");
});

test("the vault lists HEAD's history as capsules with their labels and messages", () => {
  const panel = ZonePanel.create();
  panel.update(observe(record("observation").project));
  const vault = zone(panel, "vault");
  assert.equal(vault.querySelectorAll(".cap").length, Number(vault.querySelector(".z-count").textContent));
  assert.equal(vault.querySelector(".cap .chash").textContent, "547cd2b");
  assert.equal(vault.querySelector(".cap .ref").textContent, "HEAD → feature");
  assert.equal(vault.querySelector(".cap .cmsg").textContent, "Add a greeting to the readme");
});

test("empty zones say what fills them", () => {
  const panel = ZonePanel.create();
  panel.update(observe(record("snapshots").one, record("snapshots").unborn));
  assert.match(zone(panel, "dock").querySelector(".zone-empty").textContent, /git add/);
  assert.match(zone(panel, "remote").querySelector(".zone-empty").textContent, /git push/);
  assert.equal(zone(panel, "remote").classList.contains("is-dormant"), false);
});

test("the legend names every state a file can show", () => {
  const panel = ZonePanel.create();
  assert.deepEqual(texts(panel.element, ".legend li"), ["no repository", "new (untracked)", "edited (modified)", "on the dock (staged)", "saved (committed)"]);
});

test("an observation that changed nothing leaves the zones' nodes in place", () => {
  const panel = ZonePanel.create();
  panel.update(observe(record("observation").project));
  const first = zone(panel, "vault").querySelector(".cap");
  panel.update(observe(record("observation").project));
  assert.equal(zone(panel, "vault").querySelector(".cap"), first);
});
