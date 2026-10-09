"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { createClock, installBrowser, load, settle } = require("./load");

const document = installBrowser();
const { EditorStrip, Strings } = load(["dom.js", "strings.js", "dialog.js", "editor-strip.js"], ["EditorStrip", "Strings"]);

function strip() {
  const clock = createClock();
  const sent = [];
  const made = EditorStrip.create({ onKeys: (keys) => sent.push(keys), timers: clock });
  document.body.replaceChildren(made.element);
  const q = (selector) => made.element.querySelector(selector);
  const all = (selector) => [...made.element.querySelectorAll(selector)];
  return { made, clock, sent, q, all };
}

const keys = (run) => run.all(".pg-strip-key").map((item) => item.textContent);
const answer = async (which) => {
  await settle();
  document.body.querySelector(`dialog button.is-${which}`).dispatchEvent(makeEvent("click"));
  await settle();
};

test("the terminal's title says which editor runs on which file, and whether vim is typing", () => {
  assert.deepEqual(EditorStrip.parse("firstcommit-editor nano checklist.txt"), { editor: "nano", path: "checklist.txt", insert: false });
  assert.deepEqual(EditorStrip.parse("firstcommit-editor vim checklist.txt insert"), { editor: "vim", path: "checklist.txt", insert: true });
  assert.deepEqual(EditorStrip.parse("firstcommit-editor vim checklist.txt"), { editor: "vim", path: "checklist.txt", insert: false });
  assert.deepEqual(EditorStrip.parse("firstcommit-editor vi -R +3 notes.txt"), { editor: "vim", path: "notes.txt", insert: false }, "vi is vim; options are not the file");
  assert.deepEqual(EditorStrip.parse("firstcommit-editor nano a.txt b.txt"), { editor: "nano", path: "a.txt b.txt", insert: false }, "two files: the whole arguments");
  assert.deepEqual(EditorStrip.parse("firstcommit-editor vim"), { editor: "vim", path: "", insert: false });
  for (const title of ["", "bash", "editor nano x", "firstcommit-editor emacs x", "firstcommit-editornano x"]) assert.equal(EditorStrip.parse(title), null, title);
});

test("with no editor running the strip is hidden", () => {
  const run = strip();
  run.made.show(null);
  assert.ok(run.made.element.hidden);
});

test("nano's strip says how to save and how to quit, in nano's keys, and never names Ctrl+W", () => {
  const run = strip();
  run.made.show({ editor: "nano", path: "checklist.txt", insert: false });
  assert.equal(run.made.element.hidden, false);
  assert.deepEqual(keys(run), ["Save: Ctrl+O, then Enter", "Quit: Ctrl+X"]);
  assert.doesNotMatch(run.made.element.textContent, /Ctrl\+W/);
  assert.equal(run.q(".pg-strip-out").textContent, "Get me out");
  assert.equal(run.q(".pg-strip-toggle"), null);
});

test("vim's strip puts save and quit first; the other keys can fold behind more keys, except Esc while typing", () => {
  const run = strip();
  run.made.show({ editor: "vim", path: "checklist.txt", insert: false });
  assert.deepEqual(keys(run), ["Save and quit: Esc, then :wq Enter", "Type: press i", "Leave typing mode: Esc", "Quit without saving: Esc, then :q! Enter"]);
  assert.deepEqual(run.all(".pg-strip-key.is-more").map((item) => item.textContent), keys(run).slice(1));
  const toggle = run.q(".pg-strip-toggle");
  assert.equal(toggle.textContent, "more keys");
  assert.equal(toggle.getAttribute("aria-expanded"), "false");
  toggle.dispatchEvent(makeEvent("click"));
  assert.ok(run.made.element.classList.contains("is-open"));
  assert.equal(toggle.getAttribute("aria-expanded"), "true");
  run.made.show({ editor: "vim", path: "checklist.txt", insert: true });
  const leave = run.all(".pg-strip-key").find((item) => item.textContent.startsWith("Leave typing mode"));
  assert.ok(leave.classList.contains("is-always"));
  assert.ok(run.made.element.classList.contains("is-open"), "the open fold stays open");
});

test("Get me out asks first, and Keep editing sends nothing", async () => {
  const run = strip();
  run.made.show({ editor: "vim", path: "checklist.txt", insert: true });
  run.q(".pg-strip-out").dispatchEvent(makeEvent("click"));
  await settle();
  const dialog = document.body.querySelector("dialog");
  assert.match(dialog.textContent, /Quit vim without saving\?.*Your changes to checklist.txt are lost\./);
  assert.equal(dialog.querySelector("button.is-cancel").textContent, "Keep editing");
  assert.equal(dialog.querySelector("button.is-confirm").textContent, "Quit without saving");
  await answer("cancel");
  assert.deepEqual(run.sent, []);
});

test("in vim, Quit without saving types Esc, :q! and Enter", async () => {
  const run = strip();
  run.made.show({ editor: "vim", path: "checklist.txt", insert: true });
  run.q(".pg-strip-out").dispatchEvent(makeEvent("click"));
  await answer("confirm");
  assert.deepEqual(run.sent, ["\x1b:q!\r"]);
});

test("in nano, Quit without saving types Ctrl+X, then N only if nano is still asking", async () => {
  const run = strip();
  run.made.show({ editor: "nano", path: "checklist.txt", insert: false });
  run.q(".pg-strip-out").dispatchEvent(makeEvent("click"));
  await answer("confirm");
  assert.deepEqual(run.sent, ["\x18"]);
  await run.clock.advance(1000);
  assert.deepEqual(run.sent, ["\x18", "n"]);

  const unchanged = strip();
  unchanged.made.show({ editor: "nano", path: "checklist.txt", insert: false });
  unchanged.q(".pg-strip-out").dispatchEvent(makeEvent("click"));
  await answer("confirm");
  unchanged.made.show(null);
  await unchanged.clock.advance(1000);
  assert.deepEqual(unchanged.sent, ["\x18"], "nano left at once: no N for the shell");
});

test("the strip speaks Spanish", () => {
  Strings.use("es");
  try {
    const run = strip();
    run.made.show({ editor: "nano", path: "checklist.txt", insert: false });
    assert.deepEqual(keys(run), ["Guardar: Ctrl+O, después Enter", "Salir: Ctrl+X"]);
    assert.equal(run.q(".pg-strip-out").textContent, "Sácame de aquí");
  } finally {
    Strings.use("en");
  }
});
