"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

installBrowser();
const { LivePanel } = load(["dom.js", "markup.js", "map.js", "live.js"], ["LivePanel"]);

const clockAt = (text) => () => new Date(`2026-10-06T${text}`);
const said = (kind, ...spans) => ({ kind, text: [{ kind: "para", spans: spans.map((span) => (Array.isArray(span) ? { text: span[0], code: true } : { text: span, code: false })) }] });

test("a batch of events goes on top of the feed in its own order, and the feed keeps the newest", () => {
  const first = [said("a", "one")];
  const second = [said("b", "two"), said("c", "three")];
  let feed = LivePanel.mergeEvents([], first, 1, 2);
  feed = LivePanel.mergeEvents(feed, second, 2, 2);
  assert.deepEqual(feed.map((event) => [event.kind, event.at]), [["b", 2], ["c", 2]]);
});

test("an observation draws the player's repository, the stand-in GitHub and the three areas", () => {
  const panel = LivePanel.create({ now: clockAt("10:00:00") });
  const observation = record("observation");
  panel.update(observation);
  const text = panel.element.textContent;
  assert.ok(text.includes(observation.project.commits[0].subject));
  assert.match(text, /GitHub/);
  assert.equal(panel.element.querySelectorAll("svg.map-graph").length, 2);
  assert.ok(text.includes("todo.txt"));
});

test("without a stand-in GitHub only the player's repository is drawn", () => {
  const panel = LivePanel.create();
  panel.update({ ...record("observation"), github: null });
  assert.equal(panel.element.querySelectorAll("svg.map-graph").length, 1);
  assert.equal(panel.element.querySelector(".live-github").hidden, true);
});

test("a new commit is marked new and reported, and an unchanged repository is not redrawn", () => {
  const changes = [];
  const panel = LivePanel.create({ onChange: (change) => changes.push(change) });
  const observation = record("observation");
  const newest = observation.project.commits.shift();
  observation.project.refs[0].target = observation.project.commits[0].hash;
  observation.project.head = observation.project.commits[0].hash;
  panel.update({ ...observation, events: [] });
  const graph = panel.element.querySelector("svg.map-graph");
  panel.update({ ...observation, events: [] });
  assert.equal(panel.element.querySelector("svg.map-graph"), graph);
  panel.update(record("observation"));
  assert.equal(panel.element.querySelectorAll(".map-commit.is-new").length, 1);
  assert.equal(panel.element.querySelector(".map-commit.is-new").getAttribute("data-hash"), newest.hash);
  assert.deepEqual(changes.map((change) => change.newCommits), [0, 0, 1]);
});

test("what just happened lists the events newest first, with the time they were seen", () => {
  let now = "10:00:00";
  const panel = LivePanel.create({ now: () => clockAt(now)() });
  assert.match(panel.element.textContent, /Nothing yet/);
  panel.update({ ...record("observation"), events: [said("file-created", "You created ", ["a.txt"], ".")] });
  now = "10:00:05";
  panel.update({ ...record("observation"), events: [said("file-staged", ["a.txt"], " is staged.")] });
  const items = [...panel.element.querySelectorAll(".feed li")];
  assert.deepEqual(items.map((item) => item.getAttribute("data-kind")), ["file-staged", "file-created"]);
  assert.match(items[0].textContent, /a\.txt is staged\./);
  assert.equal(items[0].querySelector("code").textContent, "a.txt");
  assert.ok(items[0].classList.contains("is-fresh"));
  assert.ok(!items[1].classList.contains("is-fresh"));
  assert.equal(panel.element.querySelector("[aria-live]").textContent, "a.txt is staged.");
});
