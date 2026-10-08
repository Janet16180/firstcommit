"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const { FolderRow, Strings } = load(["dom.js", "strings.js", "folder-row.js"], ["FolderRow", "Strings"]);

/* A file as a snapshot lists it: `folder` is null once it left the working folder. */
const file = (path, { folder = "f1", ignored = false } = {}) => ({ path, head: "h", index: "h", folder, head_mode: null, index_mode: null, folder_mode: null, ignored, conflicted: false, repository: false, index_change: null, folder_change: null });
const chips = (row) => [...row.element.querySelectorAll(".folder-file")].map((chip) => [chip.textContent, chip.className.replace("folder-file", "").trim()]);

test("the row lists the files in the working folder, not the ones Git ignores or the folder lacks", () => {
  const row = FolderRow.create();
  row.update([file("engine.txt"), file("notes.txt"), file("sim.log", { ignored: true }), file("old.txt", { folder: null })]);
  assert.deepEqual(chips(row), [["engine.txt", ""], ["notes.txt", ""]]);
  assert.equal(row.element.querySelector(".folder-name").textContent, "Your working folder");
});

test("after a switch, a file that left stays struck through and one that came is marked new, until the folder changes again", () => {
  const row = FolderRow.create();
  row.update([file("engine.txt"), file("notes.txt")]);
  row.update([file("lights.txt"), file("notes.txt")]);
  assert.deepEqual(chips(row), [["lights.txt", "is-new"], ["notes.txt", ""], ["engine.txt", "is-gone"]]);
  row.update([file("lights.txt"), file("notes.txt")]);
  assert.deepEqual(chips(row), [["lights.txt", "is-new"], ["notes.txt", ""], ["engine.txt", "is-gone"]]);
  row.update([file("notes.txt")]);
  assert.deepEqual(chips(row), [["notes.txt", ""], ["lights.txt", "is-gone"]]);
});

test("the row speaks Spanish when the page does", () => {
  Strings.use("es");
  try {
    const row = FolderRow.create();
    row.update([file("notes.txt")]);
    assert.equal(row.element.querySelector(".folder-name").textContent, "Tu carpeta de trabajo");
  } finally {
    Strings.use("en");
  }
});
