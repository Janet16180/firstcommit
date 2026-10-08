"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { httpError, installBrowser, load, settle } = require("./load");
const Pg = require("./playground-records");

installBrowser();
const { KeepPanel, Strings } = load(["dom.js", "strings.js", "keep-panel.js"], ["KeepPanel", "Strings"]);

const CLEAN = "LAUNCH CHECKLIST\n1. Seal the hatch\n4. Course: the Moon\n5. Music: off\n";

function panel({ write = async () => ({}) } = {}) {
  const seen = { writes: [], typed: [] };
  const made = KeepPanel.create({
    onWrite: async (request) => {
      seen.writes.push(request);
      return write(request);
    },
    onType: (line) => seen.typed.push(line),
  });
  const q = (selector) => made.element.querySelector(selector);
  const all = (selector) => [...made.element.querySelectorAll(selector)];
  const click = (selector) => q(selector).dispatchEvent(makeEvent("click"));
  const show = (more = {}) => made.update({ person: "you", marked: [Pg.marked()], texts: [], editing: null, ...more });
  return { made, seen, q, all, click, show };
}

const words = (nodes) => nodes.map((node) => node.textContent);

test("the panel shows the file as git wrote it: the merged lines untagged, each block with its two sides tagged, the long hash shortened", () => {
  const run = panel();
  run.show();
  assert.match(run.q(".keep-outside").textContent, /Git merged them on its own/);
  assert.equal(run.q(".keep-head").textContent, "checklist.txtconflict: 1 block");
  assert.deepEqual(words(run.all(".keep-line .keep-text")), ["LAUNCH CHECKLIST", "1. Seal the hatch", "<<<<<<< HEAD", "4. Course: the Moon", "=======", "4. Course: Jupiter", ">>>>>>> 94b6459…", "5. Music: off"]);
  assert.equal(run.q(".keep-line[data-part=\"theirs-end\"] .keep-text").getAttribute("title"), ">>>>>>> 94b6459f310f9ec74b15d5f70e207bdf95b25026");
  assert.deepEqual(words(run.all(".keep-line[data-part=\"ours\"] .keep-tag")), ["You"]);
  assert.deepEqual(words(run.all(".keep-line[data-part=\"theirs\"] .keep-tag")), ["Alex"]);
  assert.equal(run.all(".keep-line[data-part=\"same\"] .keep-tag").length, 0);
});

test("picking a side only marks lines: the other side is struck, the markers fade, and Write becomes ready", () => {
  const run = panel();
  run.show();
  assert.ok(run.q(".keep-write").disabled);
  run.click(".keep-pick[data-choice=\"yours\"]");
  assert.equal(run.q(".keep-pick[data-choice=\"yours\"]").getAttribute("aria-pressed"), "true");
  assert.ok(run.q(".keep-line[data-part=\"theirs\"]").classList.contains("is-dropped"));
  assert.ok(run.q(".keep-line[data-part=\"ours\"]").classList.contains("is-dropped") === false);
  assert.equal(run.all(".keep-line.is-marker.is-gone").length, 3);
  assert.equal(run.q(".keep-write").disabled, false);
  assert.equal(run.q(".keep-write").textContent, "Write this into checklist.txt");
  assert.equal(run.seen.writes.length, 0);
});

test("Write sends the picks with the text the panel read, and the page then says what to type", async () => {
  const run = panel();
  run.show();
  run.click(".keep-pick[data-choice=\"both\"]");
  run.click(".keep-write");
  await settle();
  assert.deepEqual(run.seen.writes, [{ file: "checklist.txt", read: "r1", choices: ["both"] }]);
  run.show({ marked: [], texts: [{ path: "checklist.txt", folder: CLEAN, index: null }] });
  assert.equal(run.q(".keep-head").textContent, "checklist.txt, as it is nowno markers left");
  assert.deepEqual(words(run.all(".keep-line .keep-text")), ["LAUNCH CHECKLIST", "1. Seal the hatch", "4. Course: the Moon", "5. Music: off"]);
  assert.equal(run.q(".keep-message").textContent, "Written from your picks. Next: type git add checklist.txt, then git commit. The page never runs git for you.");
});

test("a file whose markers went another way (an editor) is shown as it is now, without saying the picks wrote it", () => {
  const run = panel();
  run.show();
  run.show({ marked: [], texts: [{ path: "checklist.txt", folder: CLEAN, index: null }] });
  assert.match(run.q(".keep-message").textContent, /^Next: type git add checklist.txt/);
});

test("a refused Write (the file changed) clears the picks and makes Look again the main button", async () => {
  const run = panel({ write: async () => {
    throw httpError(409, "changed");
  } });
  run.show();
  run.click(".keep-pick[data-choice=\"yours\"]");
  run.click(".keep-write");
  await settle();
  assert.match(run.q(".keep-message.is-error").textContent, /changed after this panel last read it/);
  assert.ok(run.q(".keep-look").classList.contains("btn-primary"));
  assert.ok(run.q(".keep-write").disabled);
  assert.equal(run.q(".keep-pick[aria-pressed=\"true\"]"), null);
  run.show({ marked: [Pg.marked("r2")] });
  assert.ok(run.q(".keep-look"), "Look again stays until pressed");
  run.click(".keep-look");
  assert.equal(run.q(".keep-look"), null);
  assert.equal(run.q(".keep-message"), null);
});

test("a new read of the file drops picks made on the old text", () => {
  const run = panel();
  run.show();
  run.click(".keep-pick[data-choice=\"theirs\"]");
  run.show({ marked: [Pg.marked("r2")] });
  assert.equal(run.q(".keep-pick[aria-pressed=\"true\"]"), null);
  run.click(".keep-pick[data-choice=\"theirs\"]");
  run.show({ marked: [Pg.marked("r2")] });
  assert.ok(run.q(".keep-pick[data-choice=\"theirs\"][aria-pressed=\"true\"]"), "the same read keeps them");
});

test("while an editor has the file, the panel greys, says it waits, clears the picks and offers no Write", () => {
  const run = panel();
  run.show();
  run.click(".keep-pick[data-choice=\"yours\"]");
  run.show({ editing: { editor: "vim", path: "checklist.txt" } });
  assert.ok(run.made.element.classList.contains("is-waiting"));
  assert.equal(run.q(".keep-message").textContent, "checklist.txt is open in vim in your terminal. The panel waits, and reads the file again when the editor saves it.");
  assert.equal(run.q(".keep-pick[aria-pressed=\"true\"]"), null);
  assert.ok(run.q(".keep-write").disabled);
  assert.ok(run.all(".keep-pick").every((button) => button.disabled));
  assert.ok(run.all(".keep-chip").every((chip) => chip.disabled));
  run.show();
  assert.equal(run.q(".keep-pick[aria-pressed=\"true\"]"), null, "cleared, not restored");
});

test("under the panel the editor way is two chips that type their command at the prompt", () => {
  const run = panel();
  run.show();
  assert.deepEqual(words(run.all(".keep-chip")), ["nano checklist.txt", "vim checklist.txt"]);
  run.click(".keep-chip[data-editor=\"vim\"]");
  assert.deepEqual(run.seen.typed, ["vim checklist.txt"]);
});

test("in Alex's repository Alex's side is the one at HEAD, and the buttons say whose", () => {
  const run = panel();
  run.show({ person: "alex" });
  assert.deepEqual(words(run.all(".keep-line[data-part=\"ours\"] .keep-tag")), ["Alex"]);
  assert.deepEqual(words(run.all(".keep-line[data-part=\"theirs\"] .keep-tag")), ["You"]);
  assert.deepEqual(words(run.all(".keep-pick")), ["Alex's", "Yours", "Both"]);
  assert.equal(run.made.element.dataset.person, "alex");
});

test("with no marked file and none seen yet, the panel says so", () => {
  const run = panel();
  run.show({ marked: [] });
  assert.equal(run.q(".keep-none").textContent, "No file has conflict markers.");
});

test("the panel speaks Spanish", () => {
  Strings.use("es");
  try {
    const run = panel();
    run.show();
    assert.equal(run.q(".keep-write").textContent, "Escribir esto en checklist.txt");
    assert.deepEqual(words(run.all(".keep-pick")), ["La tuya", "La de Alex", "Las dos"]);
  } finally {
    Strings.use("en");
  }
});

test("a file still listed with no blocks left (an editor took the markers out, git add not yet typed) is shown as it is now", () => {
  const run = panel();
  run.show();
  const edited = { path: "checklist.txt", read: "r2", parts: [{ kind: "clean", lines: ["LAUNCH CHECKLIST", "4. Course: the Moon"] }] };
  run.show({ marked: [edited] });
  assert.equal(run.q(".keep-head").textContent, "checklist.txt, as it is nowno markers left");
  assert.deepEqual(words(run.all(".keep-line .keep-text")), ["LAUNCH CHECKLIST", "4. Course: the Moon"]);
  assert.match(run.q(".keep-message").textContent, /^Next: type git add checklist.txt/);
  assert.equal(run.q(".keep-write"), null);
});
