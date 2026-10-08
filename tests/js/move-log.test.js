"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const { MoveLog, Strings } = load(["dom.js", "strings.js", "move-log.js"], ["MoveLog", "Strings"]);

const hash = (name) => `${name}`.padEnd(40, "0");
/* A move as the observation gives it, with the line git printed for it at HEAD@{at}. */
const entry = (to, message, at, decoration = "") => ({ old: hash("0"), new: hash(to), message, line: `${hash(to).slice(0, 7)}${decoration} HEAD@{${at}}: ${message}` });
/* HEAD's moves, newest first. */
const reflog = () => [entry("a1", "reset: moving to origin/main", 0, " (HEAD -> main, origin/main)"), entry("b2", "commit: Survey day 2", 1), entry("b1", "commit: Survey day 1", 2), entry("a1", "clone: from github.com/moonbase/project.git", 3)];
const ghost = (name) => ({ hash: hash(name), short: hash(name).slice(0, 7), parents: [], subject: name, author: "You", time: 0 });
const lines = (log) => [...log.element.querySelectorAll(".movelog-row")].map((row) => row.querySelector(".movelog-line").textContent);

test("before git reflog is typed the move log says how to read it, and shows no row", () => {
  const log = MoveLog.create();
  log.update({ reflog: reflog(), ghosts: [], typed: false, marks: true });
  assert.equal(log.element.querySelectorAll(".movelog-row").length, 0);
  assert.equal(log.element.querySelector(".movelog-empty").textContent, "Type git reflog to read the move log.");
  assert.equal(log.element.querySelector(".movelog-empty code").textContent, "git reflog");
});

test("once typed, its rows read exactly as git reflog printed them, newest first, HEAD@{n} picked out", () => {
  const log = MoveLog.create();
  log.update({ reflog: reflog(), ghosts: [], typed: true, marks: true });
  assert.deepEqual(lines(log), [
    "a100000 (HEAD -> main, origin/main) HEAD@{0}: reset: moving to origin/main",
    "b200000 HEAD@{1}: commit: Survey day 2",
    "b100000 HEAD@{2}: commit: Survey day 1",
    "a100000 HEAD@{3}: clone: from github.com/moonbase/project.git",
  ]);
  assert.deepEqual([...log.element.querySelectorAll(".movelog-ref")].map((ref) => ref.textContent), ["HEAD@{0}", "HEAD@{1}", "HEAD@{2}", "HEAD@{3}"]);
});

test("the rows light up one after another the first time, in step with the terminal's lines", () => {
  const log = MoveLog.create();
  log.update({ reflog: reflog(), ghosts: [], typed: true, marks: true });
  const rows = [...log.element.querySelectorAll(".movelog-row")];
  assert.ok(rows.every((row) => row.classList.contains("is-lit")));
  assert.deepEqual(rows.map((row) => row.style.getPropertyValue("--step")), ["0", "1", "2", "3"]);
});

test("a row whose commit no name leads to says so, unless the level keeps quiet", () => {
  const log = MoveLog.create();
  log.update({ reflog: reflog(), ghosts: [ghost("b2"), ghost("b1")], typed: true, marks: true });
  assert.deepEqual([...log.element.querySelectorAll(".movelog-row")].map((row) => Boolean(row.querySelector(".movelog-noname"))), [false, true, true, false]);
  log.update({ reflog: reflog(), ghosts: [ghost("b2"), ghost("b1")], typed: true, marks: false });
  assert.equal(log.element.querySelector(".movelog-noname"), null);
});

test("picking a row tells which commit it landed on, and the pick stays on that move as newer rows push it down", () => {
  const picks = [];
  const log = MoveLog.create({ onPick: (picked) => picks.push(picked) });
  log.update({ reflog: reflog(), ghosts: [], typed: true, marks: true });
  log.element.querySelectorAll(".movelog-row")[1].click();
  assert.deepEqual(picks, [hash("b2")]);
  const renumbered = reflog().map((move, at) => ({ ...move, line: move.line.replace(`HEAD@{${at}}`, `HEAD@{${at + 1}}`) }));
  log.update({ reflog: [entry("b2", "checkout: moving from main to survey", 0), ...renumbered], ghosts: [], typed: true, marks: true });
  const picked = log.element.querySelector(".movelog-row.is-picked");
  assert.equal(picked.querySelector(".movelog-line").textContent, "b200000 HEAD@{2}: commit: Survey day 2");
  assert.ok(log.element.querySelectorAll(".movelog-row")[0].classList.contains("is-fresh"));
  assert.equal(log.element.querySelector(".movelog-row.is-lit"), null);
});

test("the move log speaks Spanish around git's own words", () => {
  Strings.use("es");
  try {
    const log = MoveLog.create();
    log.update({ reflog: reflog(), ghosts: [ghost("b2")], typed: true, marks: true });
    assert.equal(log.element.getAttribute("aria-label"), "El log de movimientos");
    assert.equal(log.element.querySelector(".movelog-noname").textContent, "sin nombre");
    assert.equal(lines(log)[0], "a100000 (HEAD -> main, origin/main) HEAD@{0}: reset: moving to origin/main");
  } finally {
    Strings.use("en");
  }
});
