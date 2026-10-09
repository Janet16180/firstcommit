"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { createClock, httpError, installBrowser, load, settle } = require("./load");
const Pg = require("./playground-records");

const document = installBrowser();
const { MergeTool, Strings } = load(["dom.js", "strings.js", "keep-panel.js", "merge-tool.js"], ["MergeTool", "Strings"]);

const TITLE = "firstcommit-mergetool checklist.txt";

function tool({ write = async () => ({}) } = {}) {
  const clock = createClock();
  const seen = { writes: [], cancels: 0, opened: [], closed: [] };
  const made = MergeTool.create({
    timers: clock,
    now: clock.now,
    onWrite: async (request) => {
      seen.writes.push(request);
      return write(request);
    },
    onCancel: () => (seen.cancels += 1),
    onOpen: (path) => seen.opened.push(path),
    onClose: (why) => seen.closed.push(why),
  });
  document.body.replaceChildren(made.element);
  const q = (selector) => made.element.querySelector(selector);
  const click = (selector) => q(selector).dispatchEvent(makeEvent("click"));
  const show = () => made.update({ person: "you", marked: [Pg.marked()], texts: [] });
  return { made, clock, seen, q, click, show };
}

test("the terminal's title names the file the game's merge tool waits for", () => {
  assert.equal(MergeTool.parse(TITLE), "checklist.txt");
  assert.equal(MergeTool.parse("firstcommit-mergetool docs/launch plan.txt"), "docs/launch plan.txt");
  for (const other of ["", "firstcommit-editor vim checklist.txt", "firstcommit-mergetool", "bash"]) assert.equal(MergeTool.parse(other), null);
});

test("the panel stays hidden until the tool's title comes, then shows the file it waits for, with Cancel and no editor chips", () => {
  const run = tool();
  run.show();
  assert.equal(run.made.element.hidden, true);
  run.made.title(TITLE);
  assert.equal(run.made.element.hidden, false);
  assert.equal(run.made.isOpen(), true);
  assert.deepEqual(run.seen.opened, ["checklist.txt"]);
  assert.match(run.q(".mtool-bar").textContent, /Merge tool.*firstcommit.*checklist\.txt/);
  assert.equal(run.q(".keep-head").textContent, "checklist.txtconflict: 1 block");
  assert.equal(run.q(".keep-chip"), null);
  assert.match(run.q(".mtool-foot").textContent, /training tool/);
  assert.match(run.q(".mtool-wait").textContent, /Ctrl-C/);
});

test("the same title sent again keeps the panel and its picks, and tells nobody it opened twice", () => {
  const run = tool();
  run.show();
  run.made.title(TITLE);
  run.click(".keep-pick[data-choice=\"theirs\"]");
  run.made.title(TITLE);
  run.show();
  assert.deepEqual(run.seen.opened, ["checklist.txt"]);
  assert.equal(run.q(".keep-pick[data-choice=\"theirs\"]").getAttribute("aria-pressed"), "true");
});

test("Write sends the picks for the file the tool waits for", async () => {
  const run = tool();
  run.show();
  run.made.title(TITLE);
  run.click(".keep-pick[data-choice=\"yours\"]");
  run.click(".keep-write");
  await settle();
  assert.deepEqual(run.seen.writes, [{ file: "checklist.txt", read: Pg.marked().read, choices: ["yours"] }]);
});

test("a refused Write leaves the panel open with Look again", async () => {
  const run = tool({ write: async () => Promise.reject(httpError(409, { kind: "changed" })) });
  run.show();
  run.made.title(TITLE);
  run.click(".keep-pick[data-choice=\"yours\"]");
  run.click(".keep-write");
  await settle();
  assert.equal(run.made.isOpen(), true);
  assert.ok(run.q(".keep-look"));
});

test("Cancel asks the terminal to cancel and leaves closing to the tool's own title", () => {
  const run = tool();
  run.show();
  run.made.title(TITLE);
  run.click(".mtool-cancel");
  assert.equal(run.seen.cancels, 1);
  assert.equal(run.made.isOpen(), true);
  run.made.title("");
  assert.equal(run.made.isOpen(), false);
  assert.equal(run.made.element.hidden, true);
  assert.deepEqual(run.seen.closed, ["ended"]);
});

test("a title not sent again for five seconds is stale: the panel closes", async () => {
  const run = tool();
  run.made.title(TITLE);
  await run.clock.advance(2000);
  run.made.title(TITLE);
  await run.clock.advance(4900);
  assert.equal(run.made.isOpen(), true);
  await run.clock.advance(200);
  assert.equal(run.made.isOpen(), false);
  assert.deepEqual(run.seen.closed, ["expired"]);
});

test("a title heard earlier opens the panel only for what is left of its five seconds", async () => {
  const run = tool();
  await run.clock.advance(10000);
  run.made.title(TITLE, 4000);
  assert.equal(run.made.isOpen(), false);
  run.made.title(TITLE, 7000);
  assert.equal(run.made.isOpen(), true);
  await run.clock.advance(2100);
  assert.equal(run.made.isOpen(), false);
});

test("the panel closes with the terminal, and says why", () => {
  const run = tool();
  run.made.title(TITLE);
  run.made.closed();
  assert.equal(run.made.isOpen(), false);
  assert.deepEqual(run.seen.closed, ["terminal"]);
  run.made.closed();
  assert.deepEqual(run.seen.closed, ["terminal"]);
});

test("another program's title closes the panel, as the tool is no longer the one running", () => {
  const run = tool();
  run.made.title(TITLE);
  run.made.title("firstcommit-editor vim checklist.txt");
  assert.equal(run.made.isOpen(), false);
});

test("the panel speaks Spanish to a Spanish player", () => {
  Strings.use("es");
  try {
    const run = tool();
    run.show();
    run.made.title(TITLE);
    assert.match(run.q(".mtool-bar").textContent, /Herramienta de merge/);
    assert.match(run.q(".mtool-cancel").textContent, /Cancelar/);
  } finally {
    Strings.use("en");
  }
});
