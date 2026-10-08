"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const { PastPanel, Strings } = load(["dom.js", "strings.js", "past-panel.js"], ["PastPanel", "Strings"]);

const read = (more = {}) => ({ rev: "ccf9485", commit: "ccf94851a5a48045b27ccbc2005bd27b840515f7", subject: "Log the fuel after Phobos", text: "fuel: 60%\n", ...more });

function panel(file, past) {
  const made = PastPanel.create();
  made.update({ file, past });
  return { made, q: (selector) => made.element.querySelector(selector) };
}

test("before anything is read, the panel says how to fill it", () => {
  const run = panel("fuel.txt", null);
  assert.equal(run.q(".past-title").textContent, "fuel.txt as it was then");
  assert.equal(run.q(".past-empty").textContent, "Nothing read yet. git show <commit>:fuel.txt prints the file exactly as that commit recorded it.");
  assert.equal(run.q(".past-text"), null);
});

test("a read file shows exactly what git printed, titled with its commit, and says the folder is not changed", () => {
  const run = panel("fuel.txt", read());
  assert.equal(run.q(".past-title").textContent, "fuel.txt as it was in \"Log the fuel after Phobos\"");
  assert.equal(run.q(".past-text").textContent, "fuel: 60%");
  assert.equal(run.q(".past-note").textContent, "Read from the commit. Your folder is not changed.");
  assert.equal(run.made.element.dataset.state, "read");
});

test("a commit without the file says the file is not there", () => {
  const run = panel("keys.txt", read({ rev: "HEAD", subject: "Remove the keys", text: null }));
  assert.equal(run.q(".past-title").textContent, "keys.txt as it was in \"Remove the keys\"");
  assert.equal(run.q(".past-missing").textContent, "Not there: this commit has no keys.txt.");
  assert.equal(run.q(".past-text"), null);
  assert.equal(run.made.element.dataset.state, "missing");
});

test("a commit git does not know is named as typed", () => {
  const run = panel("fuel.txt", read({ rev: "zzz", commit: null, subject: null, text: null }));
  assert.equal(run.q(".past-title").textContent, "fuel.txt as it was then");
  assert.equal(run.q(".past-missing").textContent, "Git knows no commit called zzz.");
});

test("the panel speaks Spanish", () => {
  Strings.use("es");
  try {
    const run = panel("fuel.txt", read());
    assert.equal(run.q(".past-title").textContent, "fuel.txt como estaba en \"Log the fuel after Phobos\"");
    assert.equal(run.q(".past-note").textContent, "Leído del commit. Tu carpeta no cambia.");
  } finally {
    Strings.use("en");
  }
});
