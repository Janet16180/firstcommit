"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { createClock, installBrowser, load, record } = require("./load");

installBrowser();
const { Pictures } = load(["dom.js", "strings.js", "chain.js", "folder-row.js", "desk.js", "move-log.js", "target-chart.js", "git-graph.js", "sides.js", "pictures.js"], ["Pictures"]);

/* A level's pictures as LevelView.pictures gives them: the chain alone unless a test says more. */
const spec = (more = {}) => ({ large: "chain", small: null, folder: false, mothership: false, alex: false, ghosts: false, kept: null, lines: [], graph: false, target: null, whatif: null, ...more });
/* The sample observation, with the fields the pictures read; `typed` are this tick's lines. */
const observed = (typed = [], more = {}) => ({ ...record("observation"), commands: typed.map((line) => ({ line, status: 0 })), texts: [], graph: null, ...more });
const shown = (pictures) => [".pictures-large", ".pictures-small"].flatMap((slot) => [...pictures.element.querySelector(slot).children]).map((node) => node.className.split(" ")[0]);
const made = (more, observation = observed(), progress = { look: [], passed: [] }) => {
  const pictures = Pictures.create(spec(more));
  pictures.update(observation, progress);
  return pictures;
};

test("a level shows its large picture, and its small one under it, and nothing else", () => {
  assert.deepEqual(shown(made()), ["chain"]);
  assert.deepEqual(shown(made({ large: "desk", small: "chain" })), ["desk", "chain"]);
  assert.ok(made({ large: "desk", small: "chain" }).element.querySelector(".pictures-small .chain"));
});

test("the folder row sits under the chain when the level wants it", () => {
  assert.equal(made().element.querySelector(".folder-row"), null);
  const pictures = made({ folder: true });
  assert.deepEqual([...pictures.element.querySelectorAll(".pictures-large .folder-row .folder-file")].map((chip) => chip.textContent), record("observation").project.files.filter((file) => file.folder !== null && !file.ignored).map((file) => file.path));
});

test("the mothership's pin is drawn only in a level that has it on", () => {
  assert.equal(made().element.querySelector(".chain-rows .chain-pin"), null);
  assert.ok(made({ mothership: true }).element.querySelector(".chain-rows .chain-pin.is-mothership"));
});

test("typing git log lights the walk down the chain, until the next lines", () => {
  const pictures = Pictures.create(spec());
  pictures.update(observed(["git log --oneline"]), { look: [], passed: [] });
  assert.ok(pictures.element.querySelector(".chain-wire.is-walk"));
  pictures.update(observed([]), { look: [], passed: [] });
  assert.ok(pictures.element.querySelector(".chain-wire.is-walk"));
  pictures.update(observed(["git status"]), { look: [], passed: [] });
  assert.equal(pictures.element.querySelector(".chain-wire.is-walk"), null);
});

test("the move log waits for git reflog, then keeps its rows, and the commits only it reaches appear on the chain with it", () => {
  const ghost = { hash: "f".repeat(40), short: "fffffff", parents: [record("observation").project.head], subject: "Survey day 1", author: "You", time: 9 };
  const pictures = Pictures.create(spec({ large: "movelog", small: "chain", ghosts: true }));
  pictures.update(observed([], { ghosts: [ghost] }), { look: [], passed: [] });
  assert.equal(pictures.element.querySelector(".movelog-row"), null);
  assert.equal(pictures.element.querySelector(".chain-row.is-ghost"), null);
  pictures.update(observed(["git reflog"], { ghosts: [ghost] }), { look: [], passed: [] });
  assert.equal(pictures.element.querySelectorAll(".movelog-row").length, record("observation").reflog.length);
  assert.ok(pictures.element.querySelector(".chain-row.is-ghost"));
  pictures.update(observed(["git status"], { ghosts: [ghost] }), { look: [], passed: [] });
  assert.ok(pictures.element.querySelector(".movelog-row"));
});

test("picking a move rings the commit it landed on, on the chain", () => {
  const pictures = Pictures.create(spec({ large: "movelog", small: "chain" }));
  const reflog = record("observation").project.commits.map((commit) => ({ old: "", new: commit.hash, message: `commit: ${commit.subject}` }));
  pictures.update(observed(["git reflog"], { reflog }), { look: [], passed: [] });
  const row = pictures.element.querySelectorAll(".movelog-row")[1];
  row.click();
  const ringed = [...pictures.element.querySelectorAll(".chain-row.is-look")].map((each) => each.dataset.hash);
  assert.deepEqual(ringed, [row.dataset.hash]);
});

test("the goal's look rings its commit on the chain", () => {
  const subject = record("observation").project.commits[1].subject;
  const pictures = made({}, observed(), { look: [subject], passed: [] });
  assert.deepEqual([...pictures.element.querySelectorAll(".chain-row.is-look .chain-subject")].map((each) => each.textContent), [subject]);
});

test("a challenge's chart stands beside the chain", () => {
  const subject = record("observation").project.commits[0].subject;
  const pictures = made({ target: { commits: [{ id: "tip", parents: [], subject }], names: { main: "tip" }, head: "main" } });
  assert.ok(pictures.element.querySelector(".pictures-pair .target"));
  assert.equal(pictures.element.querySelectorAll(".pictures-pair .chain").length, 2);
});

test("git's own drawing appears beside the chain once the game sends it", () => {
  assert.equal(made({ graph: true }).element.querySelector(".graph"), null);
  const pictures = made({ graph: true }, observed([], { graph: ["* a0c26f8 (HEAD -> main) Add the route"] }));
  assert.ok(pictures.element.querySelector(".pictures-pair .graph .graph-line"));
});

test("the desk draws its outline once the level's step has passed, and git diff makes its red lines blink", () => {
  const texts = [{ path: "README.md", folder: "one\ntwo\n", index: "one\n" }];
  const pictures = Pictures.create(spec({ large: "desk", kept: "predict", lines: ["README.md"] }));
  pictures.update(observed([], { texts }), { look: [], passed: [] });
  assert.ok(!pictures.element.querySelector(".desk-kept").classList.contains("is-on"));
  pictures.update(observed(["git diff"], { texts }), { look: [], passed: ["predict"] });
  assert.ok(pictures.element.querySelector(".desk-kept").classList.contains("is-on"));
  assert.ok(pictures.element.querySelector(".desk-line.is-blink"));
});

test("two sides opens the conflicted files as the large picture", () => {
  const pictures = made({ large: "sides", small: "chain" });
  assert.deepEqual(shown(pictures), ["sides", "chain"]);
  assert.ok(pictures.element.querySelector(".pictures-large .sides-half"));
});

test("once its step has passed, the chain plays the level's WHAT IF for a while, then rewinds to the real chain", async () => {
  const clock = createClock();
  const branch = record("observation").project.refs.find((ref) => ref.kind === "branch" && ref.name !== record("observation").project.branch);
  const pictures = Pictures.create(spec({ whatif: { without: [branch.name], after: "reset" } }), { timers: clock });
  pictures.update(observed(), { look: [], passed: [] });
  assert.ok(!pictures.element.querySelector(".chain").classList.contains("is-whatif"));
  pictures.update(observed(), { look: [], passed: ["reset"] });
  assert.ok(pictures.element.querySelector(".chain").classList.contains("is-whatif"));
  await clock.advance(7000);
  const chain = pictures.element.querySelector(".chain");
  assert.ok(!chain.classList.contains("is-whatif"));
  assert.ok(chain.classList.contains("is-rewind"));
  pictures.update(observed(), { look: [], passed: ["reset"] });
  assert.ok(!pictures.element.querySelector(".chain").classList.contains("is-whatif"));
});
