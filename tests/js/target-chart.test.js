"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const { TargetChart, Strings } = load(["dom.js", "strings.js", "places.js", "chain.js", "target-chart.js"], ["TargetChart", "Strings"]);

const hash = (name) => `${name}`.padEnd(40, "0");
const commit = (name, parents, subject, time) => ({ hash: hash(name), short: hash(name).slice(0, 7), parents: parents.map(hash), subject, author: "You", time });
const ref = (name, at, kind = "branch") => ({ name, kind, target: hash(at) });
const commits = [commit("c", ["b"], "Try bright lights", 3), commit("d", ["b"], "Fix the route", 4), commit("b", ["a"], "Plot the route", 2), commit("a", [], "Start the project", 1)];
const project = (refs, branch) => ({ exists: true, bare: false, head: refs.find((r) => r.name === branch).target, branch, commits, refs, remotes: [], files: [] });
/* The captain's chart as LevelView.target gives it: the goal tree by the level's own labels, the
   names on it, and the one HEAD should ride. */
const target = {
  commits: [{ id: "lights", parents: ["plot"], subject: "Try bright lights" }, { id: "fix", parents: ["plot"], subject: "Fix the route" }, { id: "plot", parents: ["start"], subject: "Plot the route" }, { id: "start", parents: [], subject: "Start the project" }],
  names: { main: "fix", release: "fix", "lights-v2": "lights" },
  head: "lights-v2",
};
const checks = (chart) => [...chart.element.querySelectorAll(".target-check")].map((check) => [check.textContent, check.classList.contains("is-ok")]);

test("the chart draws the same commits with the names where they should end up, HEAD riding the one it names", () => {
  const chart = TargetChart.create();
  chart.update(project([ref("main", "d"), ref("fuel-test", "a")], "fuel-test"), target);
  const tags = (subject) => [...chart.element.querySelectorAll(".chain-row")].find((row) => row.querySelector(".chain-subject").textContent === subject);
  assert.deepEqual([...tags("Fix the route").querySelectorAll(".chain-tag")].map((tag) => tag.textContent).sort(), ["main", "release"]);
  assert.ok(tags("Try bright lights").querySelector(".chain-head"));
  assert.equal(chart.element.querySelectorAll(".chain-row").length, 4);
  assert.equal(chart.element.querySelector(".chain-legend"), null);
});

test("the counts tell how far off the chain is without saying what to type", () => {
  const chart = TargetChart.create();
  chart.update(project([ref("main", "d"), ref("fuel-test", "a")], "fuel-test"), target);
  assert.deepEqual(checks(chart), [["Names in place: 1 of 3", false], ["HEAD in place", false], ["Names the chart does not have: 1", false]]);
  assert.deepEqual([...chart.element.querySelectorAll(".chain-tag.is-placed")].map((tag) => tag.textContent), ["main"]);
});

test("every count turns green once the chain matches the chart", () => {
  const chart = TargetChart.create();
  chart.update(project([ref("main", "d"), ref("release", "d"), ref("lights-v2", "c")], "lights-v2"), target);
  assert.deepEqual(checks(chart).map(([, ok]) => ok), [true, true, true]);
  assert.equal(chart.element.querySelectorAll(".chain-tag.is-placed").length, 3);
});

test("the chart speaks Spanish when the page does", () => {
  Strings.use("es");
  try {
    const chart = TargetChart.create();
    chart.update(project([ref("main", "d")], "main"), target);
    assert.deepEqual(checks(chart).map(([words]) => words), ["Nombres en su sitio: 1 de 3", "HEAD en su sitio", "Nombres que la carta no tiene: 0"]);
    assert.equal(chart.element.querySelector(".target-title").textContent, "La carta del capitán");
  } finally {
    Strings.use("en");
  }
});

test("HEAD is in place only on the chart's name and that name's commit: switch -c from the wrong commit does not count", () => {
  const chart = TargetChart.create();
  chart.update(project([ref("main", "d"), ref("release", "d"), ref("lights-v2", "d")], "lights-v2"), target);
  assert.deepEqual(checks(chart)[1], ["HEAD in place", false]);
});

test("the chart lists side lines in the same order as your chain, so the two read side by side", () => {
  const forks = {
    commits: [{ id: "quiet", parents: ["fix"], subject: "Try a quiet engine" }, { id: "bright", parents: ["fix"], subject: "Try bright lights" }, { id: "fix", parents: [], subject: "Fix the route" }],
    names: { main: "fix" },
    head: "main",
  };
  const mine = { exists: true, bare: false, head: hash("f"), branch: "main", commits: [commit("b", ["f"], "Try bright lights", 10), commit("q", ["f"], "Try a quiet engine", 5), commit("f", [], "Fix the route", 1)], refs: [ref("main", "f")], remotes: [], files: [] };
  const chart = TargetChart.create();
  chart.update(mine, forks);
  assert.deepEqual([...chart.element.querySelectorAll(".chain-subject")].map((each) => each.textContent), ["Try bright lights", "Try a quiet engine", "Fix the route"]);
});
