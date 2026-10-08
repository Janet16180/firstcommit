"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const { PlaygroundSummary, Strings } = load(["dom.js", "strings.js", "playground-summary.js"], ["PlaygroundSummary", "Strings"]);

const hash = (name) => `${name}`.padEnd(40, "0");
const commit = (name, parents = []) => ({ hash: hash(name), short: hash(name).slice(0, 7), parents: parents.map(hash), subject: `Commit ${name}`, author: "You", time: 0 });
const ref = (name, at, kind = "branch") => ({ name, kind, target: hash(at) });
const file = (path, more = {}) => ({ path, head: "h", index: "h", folder: "h", head_mode: null, index_mode: null, folder_mode: null, ignored: false, conflicted: false, repository: true, index_change: null, folder_change: null, ...more });
/* a <- b <- c, with x off b. */
const COMMITS = [commit("c", ["b"]), commit("x", ["b"]), commit("b", ["a"]), commit("a")];
const project = ({ refs = [ref("main", "c"), ref("origin/main", "c", "remote")], branch = "main", head = null, files = [], operation = null, commits = COMMITS } = {}) => ({
  exists: true, bare: false, head: head || (refs.find((r) => r.name === branch) || { target: null }).target, branch, commits, refs, remotes: [], files, operation, stash: 0, truncated: false,
});
const line = (view, snapshot, whose = null) => PlaygroundSummary.line({ view, whose, project: snapshot });

test("a folder that is no repository says so after the view's name", () => {
  assert.equal(line("desk", { ...project(), exists: false, head: null, branch: null, commits: [], refs: [] }), "Desk · no repository yet");
});

test("the line names the view, where HEAD is, and how the branch stands against its origin/ bookmark", () => {
  assert.equal(line("chain", project()), "Chain · HEAD on main · main in step with origin/main");
  assert.equal(line("chain", project({ refs: [ref("main", "c"), ref("origin/main", "b", "remote")] })), "Chain · HEAD on main · main 1 ahead of origin/main");
  assert.equal(line("history", project({ refs: [ref("main", "a"), ref("origin/main", "c", "remote")] })), "History · HEAD on main · main 2 behind origin/main");
  assert.equal(line("history", project({ refs: [ref("main", "x"), ref("origin/main", "c", "remote")] })), "History · HEAD on main · main 1 ahead, 1 behind origin/main");
});

test("with Alex shown, the line says whose repository it describes", () => {
  assert.equal(line("chain", project(), "alex"), "Chain · Alex's repository: HEAD on main · main in step with origin/main");
  assert.equal(line("desk", project(), "you"), "Desk · Your repository: HEAD on main · main in step with origin/main");
});

test("a branch with no origin/ bookmark, and a HEAD on no branch, say only where HEAD is", () => {
  assert.equal(line("chain", project({ refs: [ref("main", "c"), ref("bright-lights", "x")], branch: "bright-lights" })), "Chain · HEAD on bright-lights");
  assert.equal(line("chain", project({ branch: null, head: hash("b") })), "Chain · HEAD on commit b000000");
});

test("a repository with no commit yet says so", () => {
  assert.equal(line("desk", project({ refs: [], commits: [], files: [file("README.md", { head: null, index: null, folder_change: "untracked" })] })), "Desk · HEAD on main · no commits yet · 1 file changed");
});

test("files changed and not committed are counted, ignored and unchanged ones are not", () => {
  const files = [file("notes.txt", { folder_change: "modified" }), file("route.txt", { index_change: "modified" }), file("crew.txt"), file("junk.log", { ignored: true, folder_change: "ignored" })];
  assert.equal(line("desk", project({ files })), "Desk · HEAD on main · main in step with origin/main · 2 files changed");
  assert.equal(line("desk", project({ files: files.slice(0, 1) })), "Desk · HEAD on main · main in step with origin/main · 1 file changed");
});

test("a merge in progress is said", () => {
  assert.equal(line("conflict", project({ operation: "merge" })), "Conflict · HEAD on main · main in step with origin/main · merge in progress");
});

test("the line speaks Spanish", () => {
  Strings.use("es");
  try {
    assert.equal(line("chain", project({ refs: [ref("main", "a"), ref("origin/main", "c", "remote")] }), "alex"), "Cadena · Repositorio de Alex: HEAD en main · main 2 por detrás de origin/main");
  } finally {
    Strings.use("en");
  }
});
