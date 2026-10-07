"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const { Typed } = load(["typed.js"], ["Typed"]);

const ok = (line) => ({ line, status: 0 });

test("the git commands of the lines that succeeded are named, in order", () => {
  assert.deepEqual(Typed.gitCommands([ok("git init"), ok("ls -a"), ok("git status")]), ["init", "status"]);
});

test("a line that failed counts for nothing", () => {
  assert.deepEqual(Typed.gitCommands([{ line: "git ad map.txt", status: 1 }]), []);
});

test("every command of a chained line counts, after git's own options and any variables", () => {
  assert.deepEqual(Typed.gitCommands([ok("git add . && GIT_EDITOR=true git -C project commit -m 'a; b'")]), ["add", "commit"]);
});

test("git by its path is git, and other programs are not", () => {
  assert.deepEqual(Typed.gitCommands([ok("/usr/bin/git push"), ok("echo git add"), ok("gitk")]), ["push"]);
});

test("a bare git names no command", () => {
  assert.deepEqual(Typed.gitCommands([ok("git")]), []);
});
