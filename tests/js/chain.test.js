"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const { Chain, Strings } = load(["dom.js", "strings.js", "chain.js"], ["Chain", "Strings"]);

const hash = (name) => `${name}`.padEnd(40, "0");
/* A commit as a snapshot lists it; `time` orders commits of the same generation. */
const commit = (name, parents = [], time = 0) => ({ hash: hash(name), short: hash(name).slice(0, 7), parents: parents.map(hash), subject: `Commit ${name}`, author: "You", time });
const ref = (name, at, kind = "branch") => ({ name, kind, target: hash(at) });
const snapshot = ({ commits, refs, branch = "main", head = null }) => ({ exists: true, bare: false, head: head ? hash(head) : refs.find((r) => r.name === branch).target, branch, commits, refs, remotes: [], files: [] });

/* a <- b <- c on main; d off b on scout. */
const forked = () => snapshot({
  commits: [commit("c", ["b"], 3), commit("d", ["b"], 4), commit("b", ["a"], 2), commit("a", [], 1)],
  refs: [ref("main", "c"), ref("scout", "d"), ref("origin/main", "b", "remote")],
});
const view = (project, more = {}) => ({ project, github: null, teammate: null, ghosts: [], show: { mothership: false, alex: false, ghosts: false }, look: [], walk: false, ...more });
const drawn = (project, more) => {
  const chain = Chain.create();
  chain.update(view(project, more));
  return chain;
};
const rows = (chain) => [...chain.element.querySelectorAll(".chain-row")];
const rowOf = (chain, name) => chain.element.querySelector(`.chain-row[data-hash="${hash(name)}"]`);
const words = (node, selector) => [...node.querySelectorAll(selector)].map((part) => part.textContent);

test("the layout puts each commit once, newest generation at the top, the trunk in the first column and a side line just above the commit it leaves", () => {
  const { rows: laid, columns } = Chain.layout(forked().commits, [hash("c")]);
  assert.deepEqual(laid.map((row) => row.commit.subject), ["Commit c", "Commit d", "Commit b", "Commit a"]);
  assert.deepEqual(laid.map((row) => row.column), [0, 1, 0, 0]);
  assert.equal(columns, 2);
});

test("two side lines off one commit each get a column of their own, kept just above the commit they leave", () => {
  const commits = [commit("e", ["b"], 5), commit("d", ["b"], 4), commit("c", ["b"], 3), commit("b", ["a"], 2), commit("a", [], 1)];
  const { rows: laid, columns } = Chain.layout(commits, [hash("c")]);
  const column = (name) => laid.find((row) => row.commit.hash === hash(name)).column;
  assert.equal(column("c"), 0);
  assert.notEqual(column("d"), column("e"));
  assert.ok(column("d") > 0 && column("e") > 0);
  assert.equal(columns, 3);
  assert.equal(laid.at(-2).commit.hash, hash("b"));
});

test("a side line runs down its own column and turns into its parent's just above the parent", () => {
  const { rows: laid } = Chain.layout(forked().commits, [hash("c")]);
  const segments = Chain.wires(laid, new Map());
  const at = (name) => segments[laid.findIndex((row) => row.commit.hash === hash(name))];
  assert.deepEqual(at("c").map((part) => [part.shape, part.from, part.to]), [["bottom", 0, 0]]);
  assert.deepEqual(at("d").map((part) => [part.shape, part.from, part.to]), [["full", 0, 0], ["bottom", 1, 1]]);
  assert.deepEqual(at("b").map((part) => [part.shape, part.from, part.to]).sort(), [["bottom", 0, 0], ["in", 1, 0], ["top", 0, 0]]);
});

test("a merge's second line leaves the merge at once and runs down the side column", () => {
  const commits = [commit("m", ["c", "d"], 5), commit("d", ["b"], 4), commit("c", ["b"], 3), commit("b", [], 2)];
  const { rows: laid } = Chain.layout(commits, [hash("m")]);
  const segments = Chain.wires(laid, new Map());
  assert.deepEqual(segments[0].map((part) => [part.shape, part.from, part.to]).sort(), [["bottom", 0, 0], ["out", 0, 1]]);
});

test("the branch HEAD rides is a filled tag behind the HEAD mark; other branches are outlined and origin's are dashed bookmarks", () => {
  const chain = drawn(forked());
  const tip = rowOf(chain, "c");
  assert.equal(tip.querySelector(".chain-head").textContent, "HEAD ▶");
  const parts = [...tip.querySelector(".chain-body").children];
  assert.equal(parts[parts.indexOf(tip.querySelector(".chain-head")) + 1].textContent, "main");
  assert.ok(tip.querySelector(".chain-tag.is-head"));
  assert.deepEqual(words(rowOf(chain, "d"), ".chain-tag:not(.is-head):not(.is-bookmark)"), ["scout"]);
  assert.deepEqual(words(rowOf(chain, "b"), ".chain-tag.is-bookmark"), ["origin/main"]);
  assert.equal(chain.element.querySelectorAll(".chain-head").length, 1);
  assert.deepEqual(rows(chain).map((row) => row.querySelector(".chain-subject").textContent), ["Commit c", "Commit d", "Commit b", "Commit a"]);
});

test("on a bare commit the HEAD mark sits on the capsule with no tag under it", () => {
  const project = { ...forked(), branch: null, head: hash("b") };
  const chain = drawn(project);
  const row = rowOf(chain, "b");
  assert.ok(row.querySelector(".chain-head"));
  assert.equal(row.querySelector(".chain-tag.is-head"), null);
});

test("the mothership's pin marks where its main really is, and its commits you lack are pink dotted, only on the mothership", () => {
  const github = snapshot({ commits: [commit("x", ["c"], 9), ...forked().commits], refs: [ref("main", "x")] });
  const chain = drawn(forked(), { github, show: { mothership: true, alex: false, ghosts: false } });
  const only = rowOf(chain, "x");
  assert.ok(only.classList.contains("is-mothership-only"));
  assert.equal(only.querySelector(".chain-only").textContent, "only on the mothership");
  assert.deepEqual(words(only, ".chain-pin.is-mothership"), ["Mothership: main"]);
  assert.equal(chain.element.querySelectorAll(".chain-rows .chain-pin").length, 1);
});

test("without the mothership on, no pin and no commit of the mothership's is drawn", () => {
  const github = snapshot({ commits: [commit("x", ["c"], 9), ...forked().commits], refs: [ref("main", "x")] });
  const chain = drawn(forked(), { github });
  assert.equal(rowOf(chain, "x"), null);
  assert.equal(chain.element.querySelector(".chain-pin"), null);
});

test("Alex's pin marks Alex's branches, in Alex's own colour class", () => {
  const teammate = snapshot({ commits: forked().commits, refs: [ref("main", "b"), ref("origin/main", "b", "remote")] });
  const chain = drawn(forked(), { teammate, show: { mothership: false, alex: true, ghosts: false } });
  assert.deepEqual(words(rowOf(chain, "b"), ".chain-pin.is-alex"), ["Alex: main"]);
  assert.equal(chain.element.querySelectorAll(".chain-rows .chain-pin").length, 1);
});

test("a commit no name leads to is drawn faded and dashed only when the level shows ghosts", () => {
  const ghost = commit("g", ["c"], 8);
  assert.equal(rowOf(drawn(forked(), { ghosts: [ghost] }), "g"), null);
  const chain = drawn(forked(), { ghosts: [ghost], show: { mothership: false, alex: false, ghosts: true } });
  assert.ok(rowOf(chain, "g").classList.contains("is-ghost"));
  const { rows: laid } = Chain.layout([ghost, ...forked().commits], [hash("c")]);
  const segments = Chain.wires(laid, new Map([[hash("g"), "ghost"]]));
  assert.ok(segments[0].every((part) => part.style === "ghost"));
});

test("the gold ring marks only what the goal asks to look at: a commit by its subject, or the HEAD mark", () => {
  const chain = drawn(forked(), { look: ["Commit b", "HEAD"] });
  assert.deepEqual(rows(chain).filter((row) => row.classList.contains("is-look")).map((row) => row.dataset.hash), [hash("b")]);
  assert.ok(chain.element.querySelector(".chain-head.is-look"));
});

test("git log's walk lights the lines from HEAD's commit down its first parents, one after another", () => {
  const chain = drawn(forked(), { walk: true });
  const lit = [...chain.element.querySelectorAll(".chain-wire.is-walk")];
  assert.ok(lit.length >= 2);
  assert.deepEqual(lit.map((wire) => wire.style.getPropertyValue("--step")).filter((step, index, all) => all.indexOf(step) === index), ["0", "1"]);
  assert.equal(drawn(forked()).element.querySelector(".chain-wire.is-walk"), null);
});

test("each row's lane draws its wire pieces stretched to the row, one column apart", () => {
  const chain = drawn(forked());
  const lane = rowOf(chain, "d").querySelector("svg.chain-lane");
  assert.equal(lane.getAttribute("preserveAspectRatio"), "none");
  assert.deepEqual([...lane.querySelectorAll("path.chain-wire")].map((path) => path.getAttribute("d")), ["M10 0 L10 100", "M32 50 L32 100"]);
  assert.equal(rowOf(chain, "d").querySelector(".chain-cap").style.getPropertyValue("--column"), "1");
});

test("the legend names only the marks the picture shows", () => {
  assert.deepEqual(words(drawn(forked()).element, ".chain-legend li").length, 4);
  const plain = snapshot({ commits: [commit("a", [], 1)], refs: [ref("main", "a")] });
  assert.equal(drawn(plain).element.querySelectorAll(".chain-legend li").length, 2);
});

test("the chain speaks Spanish when the page does", () => {
  Strings.use("es");
  try {
    const github = snapshot({ commits: [commit("x", ["c"], 9), ...forked().commits], refs: [ref("main", "x")] });
    const chain = drawn(forked(), { github, show: { mothership: true, alex: false, ghosts: false } });
    assert.equal(rowOf(chain, "x").querySelector(".chain-only").textContent, "solo en la nave nodriza");
    assert.equal(rowOf(chain, "x").querySelector(".chain-pin").textContent, "Nave nodriza: main");
    assert.equal(chain.element.getAttribute("aria-label"), "La cadena");
  } finally {
    Strings.use("en");
  }
});

test("an update with nothing new leaves the drawing alone, so a running walk is not started over", () => {
  const chain = Chain.create();
  chain.update(view(forked(), { walk: true }));
  const first = chain.element.querySelector(".chain-rows");
  chain.update(view(forked(), { walk: true }));
  assert.equal(chain.element.querySelector(".chain-rows"), first);
  chain.update(view(forked()));
  assert.notEqual(chain.element.querySelector(".chain-rows"), first);
});
