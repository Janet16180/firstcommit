"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

const document = installBrowser();
const { GuideCard } = load(["dom.js", "guide-pictures.js", "guide-card.js"], ["GuideCard"]);

const words = {
  card: {
    before: "Before",
    after: "After",
    onlyLooks: "Nothing changes: it only looks.",
    prints: "What git prints",
    silent: "(prints nothing)",
    mistake: "Common mistake",
    taught: "Where you learn it",
    related: "Related",
    conflict: "See a conflict, step by step",
    chainKey: "HEAD marks where you are; a dashed name is your bookmark of the mothership.",
    showAll: "Show all {count} lines",
    showLess: "Show fewer lines",
  },
  pictures: {
    places: { folder: "Working folder (workshop)", staging: "Staging area (cargo dock)", vault: "Repository (vault)", remote: "Remote (mothership)" },
    notYet: "not there yet",
    empty: "empty",
    head: "HEAD",
    states: { new: "new", edited: "edited", conflict: "conflict", clean: "saved" },
    ghost: "ghost",
    notYours: "mothership only",
    by: { you: "your commit", alex: "Alex's commit" },
    marks: { merge: "merge commit", revert: "undoes the one below" },
    gone: "taken off",
    mothership: "mothership",
  },
};

const desk = (staged) => ({ kind: "desk", folder: [{ name: "map.txt", state: "new" }], staging: staged ? [{ name: "map.txt" }] : [] });
const ADD = {
  command: "git add <file>",
  what: "Copies a file into the staging area.",
  tag: null,
  picture: { before: desk(false), after: desk(true) },
  runs: [[{ command: "git add map.txt", output: "" }, { command: "git status", output: "On branch main\n" }]],
  mistake: "Editing again after git add.",
  where: "Sector 2, mission 1: First cargo",
  related: ["git commit", "git status"],
  conflict: false,
};

function create(card = ADD, handlers = {}) {
  const element = GuideCard.create(card, words, { onRelated: () => {}, onConflict: () => {}, ...handlers });
  document.body.replaceChildren(element);
  return element;
}

test("a card names its command and says in one sentence what it does", () => {
  const card = create();
  assert.equal(card.querySelector(".gc-command").textContent, "git add <file>");
  assert.equal(card.querySelector(".gc-meaning").textContent, "Copies a file into the staging area.");
  assert.equal(card.getAttribute("aria-labelledby"), card.querySelector(".gc-command").id);
});

test("a card shows the picture before and after the command", () => {
  const card = create();
  const figures = card.querySelectorAll(".gc-figure");
  assert.deepEqual([...figures].map((figure) => figure.querySelector("figcaption").textContent), ["Before", "After"]);
  assert.equal(figures[0].querySelectorAll(".gp-chip").length, 1);
  assert.equal(figures[1].querySelectorAll(".gp-chip").length, 2);
});

test("a command that only looks gets one picture, which says nothing changes", () => {
  const card = create({ ...ADD, picture: { before: desk(true) } });
  const figures = card.querySelectorAll(".gc-figure");
  assert.equal(figures.length, 1);
  assert.equal(figures[0].querySelector("figcaption").textContent, "Nothing changes: it only looks.");
});

test("what git prints is the captured transcript, each command after a prompt, and a silent command says so", () => {
  const card = create();
  const terminal = card.querySelector(".gc-term");
  assert.equal(terminal.textContent, "$ git add map.txt\n(prints nothing)\n$ git status\nOn branch main\n");
  assert.deepEqual([...terminal.querySelectorAll(".gc-typed")].map((node) => node.textContent), ["git add map.txt", "git status"]);
});

test("a card names the common mistake and where the game teaches the command", () => {
  const text = create().textContent;
  assert.match(text, /Common mistake.*Editing again after git add\./);
  assert.match(text, /Where you learn it.*Sector 2, mission 1: First cargo/);
});

test("a related command is a button that asks for its card", () => {
  const asked = [];
  const card = create(ADD, { onRelated: (command) => asked.push(command) });
  const buttons = card.querySelectorAll(".gc-related button");
  assert.deepEqual([...buttons].map((button) => button.textContent), ["git commit", "git status"]);
  buttons[1].click();
  assert.deepEqual(asked, ["git status"]);
});

test("a merge's card leads to the conflict; other cards do not", () => {
  let led = 0;
  assert.equal(create().querySelector(".gc-conflict"), null);
  create({ ...ADD, conflict: true }, { onConflict: () => (led += 1) }).querySelector(".gc-conflict").click();
  assert.equal(led, 1);
});

test("a command still ahead carries its tag", () => {
  const card = create({ ...ADD, tag: "Coming up in sector 7" });
  assert.equal(card.querySelector(".gc-tag").textContent, "Coming up in sector 7");
  assert.equal(create().querySelector(".gc-tag"), null);
});

test("where the game teaches it, and the way to the conflict, come before the pictures", () => {
  const card = create({ ...ADD, conflict: true });
  const order = [...card.children].map((node) => node.className);
  assert.ok(order.indexOf("gc-where") < order.indexOf("gc-pictures"));
  assert.ok(order.indexOf("btn gc-conflict") < order.indexOf("gc-pictures"));
});

test("a chain picture comes with one line that says what HEAD and a dashed name are", () => {
  const chain = { kind: "chain", commits: [{ id: "a", col: 0, parents: [] }], names: [{ name: "main", on: "a", kind: "branch" }], head: "main" };
  assert.match(create({ ...ADD, picture: { before: chain } }).textContent, /HEAD marks where you are/);
  assert.doesNotMatch(create().textContent, /HEAD marks where you are/);
});

test("a long transcript shows its key lines, leaving out git's hints, and Show all opens the rest", () => {
  const wall = ["To ../mothership.git", " ! [rejected]        main -> main (fetch first)", "error: failed to push some refs", "hint: Updates were rejected", "hint: have locally."].join("\n") + "\n";
  const card = create({ ...ADD, runs: [[{ command: "git push", output: wall }]] });
  const terminal = card.querySelector(".gc-term");
  assert.equal(terminal.querySelectorAll(".gc-more").length, 2);
  const button = card.querySelector(".gc-show");
  assert.equal(button.textContent, "Show all 6 lines");
  assert.equal(button.getAttribute("aria-expanded"), "false");
  button.click();
  assert.ok(terminal.classList.contains("is-open"));
  assert.equal(button.getAttribute("aria-expanded"), "true");
  assert.equal(button.textContent, "Show fewer lines");
});

test("a short transcript has nothing to hide and no Show all", () => {
  const card = create();
  assert.equal(card.querySelector(".gc-show"), null);
  assert.equal(card.querySelectorAll(".gc-more").length, 0);
});
