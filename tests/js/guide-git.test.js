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

/* The transcripts where git refusing is the lesson. */
const REFUSALS = ["pull-no-rebase", "switch-refused", "switch-missing", "branch-d-refused", "branch-d-here"];

test("only the refusals a card teaches fail: every other transcript ran without a git error", () => {
  for (const [name, run] of Object.entries(GuideGit.runs)) {
    const failed = run.some(({ output }) => /^(error|fatal):/m.test(output));
    assert.equal(failed, REFUSALS.includes(name), name);
  }
});

test("the branch and merge cards' commands ran on a terminal: git log names the branches, and ls prints in columns", () => {
  assert.match(GuideGit.runs.branch.at(-1).output, /^[0-9a-f]{7} \(HEAD -> main, scout\) Plot the route$/m);
  assert.equal(GuideGit.runs.switch[0].output, "notes.txt  route.txt\n");
});

/* The branch and merge cards' transcripts, all from one story. */
const CARDS = ["branch", "switch", "switch-carry", "switch-refused", "switch-c", "switch-missing", "checkout", "checkout-b", "branch-d", "branch-d-refused", "branch-d-here", "merge-ff", "merge", "merge-no-edit", "log-graph", "log-graph-head", "log-graph-merged"];

test("the cards share one story: a commit has the same hash on every card that shows it", () => {
  const hashes = new Map();
  for (const run of CARDS.map((name) => GuideGit.runs[name])) {
    for (const { output } of run) {
      for (const [, hash, subject] of output.matchAll(/^[*|/\\ ]*([0-9a-f]{7}) (?:\([^)]*\) )?(Start the project|Plot the route|Ready the probe|Fill the tanks|Merge branch 'scout')$/gm)) {
        assert.equal(hashes.get(subject) ?? hash, hash, subject);
        hashes.set(subject, hash);
      }
    }
  }
  assert.equal(hashes.size, 5);
});

test("the merge's message is the one git hands the editor: its subject first, then git's comment lines", () => {
  const [subject, ...rest] = GuideGit.mergeMessage.trimEnd().split("\n");
  assert.equal(subject, "Merge branch 'scout'");
  assert.ok(rest.length > 0 && rest.every((line) => line.startsWith("#")));
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
