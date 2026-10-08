"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const { GuideGit } = load(["guide-git.js"], ["GuideGit"]);

test("every transcript is commands with what git printed, from one git version", () => {
  assert.match(GuideGit.version, /^git version \d/);
  for (const [name, run] of Object.entries(GuideGit.runs)) {
    assert.ok(run.length > 0, name);
    for (const { command, output } of run) {
      assert.equal(typeof command, "string", name);
      assert.equal(typeof output, "string", name);
    }
  }
});

test("no transcript shows the capture's temporary folder", () => {
  assert.doesNotMatch(JSON.stringify(GuideGit), /\/tmp\//);
  assert.match(GuideGit.runs.init[0].output, /^Initialized empty Git repository in \/home\/you\/ship\/\.git\/$/m);
});

test("the conflict has its three stages, the marked file and a merge commit with two parents for each way out", () => {
  const { conflict } = GuideGit;
  for (const key of ["base", "ours", "theirs", "markers"]) assert.ok(conflict[key].endsWith("\n"), key);
  for (const side of ["yours", "theirs", "both"]) {
    assert.doesNotMatch(conflict.resolved[side], /^(<{7}|={7}|>{7})/m, side);
    assert.equal(conflict.resolved[side].split("\n").length, conflict.base.split("\n").length + (side === "both" ? 1 : 0), side);
    const [, first, second] = conflict.head[side].split(" ");
    assert.deepEqual([first, second], [conflict.yourCommit, conflict.alexCommit], side);
  }
});

test("the data is frozen", () => {
  assert.ok(Object.isFrozen(GuideGit));
});
