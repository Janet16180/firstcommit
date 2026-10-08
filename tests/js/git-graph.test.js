"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const { GitGraph, Strings } = load(["dom.js", "strings.js", "git-graph.js"], ["GitGraph", "Strings"]);

/* What `git log --oneline --graph --all` printed, uncoloured. */
const printed = ["* 9c1f2aa (quiet-engine) Quiet the engine", "| * 5d0e9b1 (HEAD -> lights) Try bright lights", "|/", "* 61255a6 (main) Fix the route", "* ce9b38c Start the project"];

test("git's own drawing shows the lines as printed, in the terminal's face", () => {
  const graph = GitGraph.create();
  graph.update(printed, []);
  assert.deepEqual([...graph.element.querySelectorAll(".graph-line")].map((line) => line.textContent), printed);
  assert.equal(graph.element.querySelector(".graph-title").textContent, "The same tree, as git log --oneline --graph --all prints it");
});

test("the lines of the commits the chain rings light up, pairing each with its line", () => {
  const graph = GitGraph.create();
  graph.update(printed, ["Quiet the engine", "Try bright lights"]);
  assert.deepEqual([...graph.element.querySelectorAll(".graph-line")].map((line) => line.classList.contains("is-look")), [true, true, false, false, false]);
});

test("the drawing speaks Spanish around git's own lines", () => {
  Strings.use("es");
  try {
    const graph = GitGraph.create();
    graph.update(printed, []);
    assert.equal(graph.element.querySelector(".graph-title").textContent, "El mismo árbol, como lo imprime git log --oneline --graph --all");
  } finally {
    Strings.use("en");
  }
});
