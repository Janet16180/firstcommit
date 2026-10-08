"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const { Desk, Strings } = load(["dom.js", "strings.js", "desk.js"], ["Desk", "Strings"]);

/* A file as a snapshot lists it, by the blob each place holds (null: not there). */
const file = (path, head, index, folder) => ({ path, head, index, folder, head_mode: null, index_mode: null, folder_mode: null, ignored: false, conflicted: false, repository: false, index_change: null, folder_change: null });
const commit = (name, subject) => ({ hash: name.padEnd(40, "0"), short: name.padEnd(7, "0"), parents: [], subject, author: "You", time: 0 });
/* 8-1: the experiment in engine.cfg's folder copy, notes.txt staged. */
const project = (engine = "e2") => ({ exists: true, bare: false, head: "c2".padEnd(40, "0"), branch: "main", commits: [commit("c2", "Tune the engine"), commit("c1", "Start the project")], refs: [], remotes: [], files: [file("engine.cfg", "e1", "e1", engine), file("notes.txt", "n1", "n2", "n2")] });
const texts = (folder = "power=99\noverdrive=on\n") => [{ path: "engine.cfg", folder, index: "power=80\n" }];
const desk = (more = {}) => {
  const made = Desk.create();
  made.update({ project: project(), texts: texts(), lines: ["engine.cfg"], kept: false, blink: false, ...more });
  return made;
};
const card = (made, path) => [...made.element.querySelectorAll(".desk-file")].find((each) => each.querySelector(".desk-name").textContent === path);
const lines = (node) => [...node.querySelectorAll(".desk-line")].map((line) => [line.querySelector(".desk-text").textContent, line.className.replace("desk-line", "").trim()]);

test("the desk lays out the working folder, the staging area and your commits, each file tagged by where Git's copy is", () => {
  const made = desk();
  assert.deepEqual([...made.element.querySelectorAll(".desk-zone h3")].map((head) => head.textContent), ["Working folder", "Staging area", "Your commits"]);
  assert.equal(card(made, "engine.cfg").querySelector(".desk-tag").textContent, "edited");
  assert.equal(card(made, "notes.txt").querySelector(".desk-tag").textContent, "Git's copy is in the staging area");
  assert.deepEqual([...made.element.querySelectorAll(".desk-zone.is-staging .desk-name")].map((name) => name.textContent), ["notes.txt"]);
  assert.deepEqual([...made.element.querySelectorAll(".desk-commit .desk-subject")].map((name) => name.textContent), ["Tune the engine", "Start the project"]);
  assert.ok(made.element.querySelectorAll(".desk-commit")[0].querySelector(".desk-head"));
});

test("a drawn file shows its lines, those Git has no copy of in red, only here", () => {
  const made = desk();
  assert.deepEqual(lines(card(made, "engine.cfg")), [["power=99", "is-only"], ["overdrive=on", "is-only"]]);
  assert.equal(card(made, "engine.cfg").querySelector(".desk-only").textContent, "only here");
  assert.equal(card(made, "notes.txt").querySelector(".desk-line"), null);
});

test("the outline Git has a copy rounds the staging area and the commits only once the level says so", () => {
  assert.ok(!desk().element.querySelector(".desk-kept").classList.contains("is-on"));
  const made = desk({ kept: true });
  assert.ok(made.element.querySelector(".desk-kept").classList.contains("is-on"));
  assert.equal(made.element.querySelector(".desk-kept-name").textContent, "Git has a copy");
  assert.equal(made.element.querySelector(".desk-kept .desk-zone.is-folder"), null);
});

test("git diff makes the red lines blink", () => {
  assert.equal(desk({ blink: true }).element.querySelectorAll(".desk-line.is-only.is-blink").length, 2);
  assert.equal(desk().element.querySelector(".is-blink"), null);
});

test("a restore dissolves the red lines: they show as gone once, and the file is back to Git's copy", () => {
  const made = desk();
  made.update({ project: project("e1"), texts: texts("power=80\n"), lines: ["engine.cfg"], kept: true, blink: false });
  assert.deepEqual(lines(card(made, "engine.cfg")), [["power=80", ""], ["power=99", "is-gone"], ["overdrive=on", "is-gone"]]);
  assert.equal(card(made, "engine.cfg").querySelector(".desk-tag"), null);
});

test("the desk speaks Spanish when the page does", () => {
  Strings.use("es");
  try {
    const made = desk({ kept: true });
    assert.deepEqual([...made.element.querySelectorAll(".desk-zone h3")].map((head) => head.textContent), ["Carpeta de trabajo", "Staging area", "Tus commits"]);
    assert.equal(made.element.querySelector(".desk-kept-name").textContent, "Git tiene una copia");
    assert.equal(made.element.querySelector(".desk-only").textContent, "solo aquí");
  } finally {
    Strings.use("en");
  }
});

test("an update with nothing new keeps the drawing, so a blink is not started over", () => {
  const made = desk({ blink: true });
  const first = made.element.querySelector(".desk-file");
  made.update({ project: project(), texts: texts(), lines: ["engine.cfg"], kept: false, blink: true });
  assert.equal(made.element.querySelector(".desk-file"), first);
});
