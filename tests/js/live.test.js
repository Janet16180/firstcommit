"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

const document = installBrowser();
const { LivePanel, RepoMap } = load(["dom.js", "markup.js", "map.js", "live.js"], ["LivePanel", "RepoMap"]);

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

test("a map redrawn after a change plays its motion from the drawing before, and the first drawing plays none", () => {
  const plays = [];
  const theme = RepoMap.DEFAULT_THEME;
  const panel = LivePanel.create({ theme, play: (figure, before, after, options) => plays.push({ figure, before, after, ...options }) });
  const observation = record("observation");
  const older = record("observation");
  older.project.commits.shift();
  older.project.refs[0].target = older.project.commits[0].hash;
  older.project.head = older.project.commits[0].hash;
  panel.update({ ...older, events: [] });
  assert.equal(plays.length, 0);
  panel.update({ ...older, events: [] });
  assert.equal(plays.length, 0, "nothing changed, nothing plays");
  panel.update(observation);
  assert.equal(plays.length, 1);
  assert.equal(plays[0].figure, panel.element.querySelector(".live-project .repo-map"));
  assert.deepEqual([plays[0].before.commits.length, plays[0].after.commits.length, plays[0].showHead, plays[0].theme], [older.project.commits.length, observation.project.commits.length, true, theme]);
});

test("given places, the three areas part draws them instead, lit from the batch's events and played from the drawing before", () => {
  const seen = { renders: [], commands: [], plays: [] };
  const places = {
    commands: (events, before, after) => {
      seen.commands.push({ events, before, after });
      return ["commit"];
    },
    render: (observation, options) => {
      seen.renders.push({ observation, options });
      return Object.assign(document.createElement("figure"), { className: "places" });
    },
    play: (figure, transition) => seen.plays.push({ figure, transition }),
  };
  const panel = LivePanel.create({ places });
  const observation = record("observation");
  const older = { ...observation, project: { ...observation.project, commits: observation.project.commits.slice(1) }, events: [] };
  panel.update(older);
  assert.equal(seen.renders.length, 1);
  assert.deepEqual(seen.renders[0].options, { commands: [] }, "nothing lights on the first drawing");
  assert.deepEqual(seen.plays, [], "and nothing plays");
  const part = panel.element.querySelector(".live-three");
  assert.equal(part.querySelector("h3").textContent, "The four places", "the part keeps its place and names what it shows");
  assert.ok(part.querySelector("figure.places"));
  assert.equal(part.querySelector(".areas-row"), null, "no three areas strip");
  panel.update(older);
  assert.equal(seen.renders.length, 1, "nothing changed, nothing redrawn");
  panel.update(observation);
  assert.deepEqual(seen.commands, [{ events: observation.events, before: older.project, after: observation.project }]);
  assert.deepEqual(seen.renders[1].options, { commands: ["commit"] });
  assert.deepEqual(seen.renders[1].observation, { project: observation.project, github: observation.github });
  assert.equal(seen.plays.length, 1);
  assert.equal(seen.plays[0].figure, part.querySelector("figure.places"));
  assert.deepEqual(seen.plays[0].transition, { before: { project: older.project, github: older.github }, after: { project: observation.project, github: observation.github }, commands: ["commit"] });
});

test("with places, the part is called the three areas until a GitHub is there, then the four places", () => {
  const places = { commands: () => [], render: () => document.createElement("figure"), play: () => [] };
  const panel = LivePanel.create({ places });
  const part = panel.element.querySelector(".live-three");
  panel.update({ ...record("observation"), github: null });
  assert.deepEqual([part.querySelector("h3").textContent, part.getAttribute("aria-label")], ["The three areas", "The three areas"]);
  panel.update(record("observation"));
  assert.deepEqual([part.querySelector("h3").textContent, part.getAttribute("aria-label")], ["The four places", "The four places"]);
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
