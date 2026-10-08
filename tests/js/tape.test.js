"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { installBrowser, load } = require("./load");

installBrowser();
const { Tape, Strings } = load(["dom.js", "strings.js", "tape.js"], ["Tape", "Strings"]);

const hash = (n) => `${n}`.repeat(40).slice(0, 40);
const move = (old, to, message) => ({ old: old === null ? "" : hash(old), new: hash(to), message });
/* HEAD's moves as the observation gives them, newest first: start, a commit, a branch switch, a reset back. */
const reflog = () => [
  move(3, 2, "reset: moving to HEAD~1"),
  move(3, 3, "checkout: moving from main to rescue"),
  move(2, 3, "commit: Survey crater B"),
  move(null, 2, "commit (initial): Start the project"),
];
const commit = (n) => ({ hash: hash(n), short: hash(n).slice(0, 7), parents: [], subject: `c${n}`, author: "You", time: 0 });
const ticks = (tape) => [...tape.element.querySelectorAll(".tape-tick")];
const chosen = (tape) => ticks(tape).find((tick) => tick.getAttribute("aria-selected") === "true");

test("the tape runs oldest to newest, each tick named by the kind of move and the capsule it landed on", () => {
  const tape = Tape.create();
  tape.update(reflog(), []);
  assert.deepEqual(ticks(tape).map((tick) => tick.dataset.kind), ["commit", "commit", "switch", "reset"]);
  assert.deepEqual(ticks(tape).map((tick) => tick.querySelector(".tape-hash").textContent), ["2222222", "3333333", "3333333", "2222222"]);
  assert.deepEqual(ticks(tape).map((tick) => tick.querySelector(".tape-kind").textContent), ["commit", "commit", "switch", "reset"]);
});

test("the newest move is chosen at first, and the readout names it as git does, HEAD@{n}, with git's own words", () => {
  const tape = Tape.create();
  tape.update(reflog(), []);
  assert.equal(chosen(tape), ticks(tape).at(-1));
  const readout = tape.element.querySelector(".tape-read");
  assert.equal(readout.querySelector(".tape-ref").textContent, "HEAD@{0}");
  assert.equal(readout.querySelector(".tape-message").textContent, "reset: moving to HEAD~1");
  assert.equal(readout.querySelector(".tape-at").textContent, "2222222");
});

test("scrubbing chooses another tick, by a click or the arrow keys", () => {
  const tape = Tape.create();
  tape.update(reflog(), []);
  ticks(tape)[1].click();
  assert.equal(tape.element.querySelector(".tape-ref").textContent, "HEAD@{2}");
  const left = makeEvent("keydown");
  left.key = "ArrowLeft";
  tape.element.querySelector(".tape-track").dispatchEvent(left);
  assert.equal(tape.element.querySelector(".tape-ref").textContent, "HEAD@{3}");
  assert.equal(tape.element.querySelector(".tape-message").textContent, "commit (initial): Start the project");
});

test("a move to a capsule only the tape still reaches is a ghost, and the readout says so", () => {
  const tape = Tape.create();
  tape.update(reflog(), [commit(3)]);
  assert.deepEqual(ticks(tape).map((tick) => tick.classList.contains("is-ghost")), [false, true, true, false]);
  ticks(tape)[2].click();
  assert.equal(tape.element.querySelector(".tape-ghost").textContent, "Only the tape still reaches this capsule. A label on it keeps it.");
  ticks(tape)[3].click();
  assert.equal(tape.element.querySelector(".tape-ghost"), null);
});

test("a move the player chose stays chosen while the tape grows, its HEAD@{n} counting up; otherwise the newest is chosen", () => {
  const tape = Tape.create();
  tape.update(reflog().slice(1), []);
  ticks(tape)[0].click();
  tape.update(reflog(), []);
  assert.equal(tape.element.querySelector(".tape-ref").textContent, "HEAD@{3}");
  const fresh = Tape.create();
  fresh.update(reflog().slice(1), []);
  fresh.update(reflog(), []);
  assert.equal(chosen(fresh), ticks(fresh).at(-1));
});

test("with no moves yet the tape says so", () => {
  const tape = Tape.create();
  tape.update([], []);
  assert.equal(ticks(tape).length, 0);
  assert.equal(tape.element.querySelector(".tape-none").textContent, "No moves yet.");
});

test("the tape's words follow the page's language; git's own message does not change", () => {
  Strings.use("es");
  try {
    const tape = Tape.create();
    tape.update(reflog(), [commit(3)]);
    assert.deepEqual(ticks(tape).map((tick) => tick.querySelector(".tape-kind").textContent), ["commit", "commit", "cambio", "reset"]);
    assert.equal(tape.element.querySelector(".tape-message").textContent, "reset: moving to HEAD~1");
    assert.equal(tape.element.getAttribute("aria-label"), "Los movimientos de HEAD");
  } finally {
    Strings.use("en");
  }
});
