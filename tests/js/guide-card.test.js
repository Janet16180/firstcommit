"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

const document = installBrowser();
const { GuideCard } = load(["dom.js", "strings.js", "places.js", "chain.js", "guide-pictures.js", "guide-card.js"], ["GuideCard"]);

const words = require("./guide-words");

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
  assert.ok(order.indexOf("gc-actions") < order.indexOf("gc-pictures"));
  assert.ok(card.querySelector(".gc-actions .gc-conflict"));
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

/* The playground's query, read as its route reads it: pairs split on "&" and "=", each value
   URI-decoded (docs/drafts/playground/plan.md, "How it is reached"). */
function query(href) {
  const [path, search] = href.split("?");
  return { path, fields: Object.fromEntries(search.split("&").map((pair) => pair.split("=")).map(([name, value]) => [name, decodeURIComponent(value)])) };
}

test("a card links to its playground start, its view and the command to try, so the route reads them back", () => {
  const playground = { start: "changes", view: "desk", try: 'git commit -am "Fuel & air = 80%"' };
  const link = create({ ...ADD, playground }).querySelector("a.gc-try");
  assert.equal(link.textContent, "Try it in the playground");
  assert.deepEqual(query(link.getAttribute("href")), { path: "#/playground", fields: playground });
});

test("a link without a view or a command to try leaves them out", () => {
  const link = create({ ...ADD, playground: { start: "empty" } }).querySelector("a.gc-try");
  assert.equal(link.getAttribute("href"), "#/playground?start=empty");
});

test("the playground link comes before the pictures, beside where the game teaches the command", () => {
  const card = create({ ...ADD, playground: { start: "empty" } });
  const order = [...card.children].map((node) => node.className);
  assert.ok(order.indexOf("gc-actions") < order.indexOf("gc-pictures"));
});

const chainOf = (head, more = {}) => ({ kind: "chain", commits: [{ id: "plot", parents: ["start"], subject: "Plot the route" }, { id: "start", parents: [], subject: "Start the project" }], names: [{ name: "main", on: "plot", kind: "branch" }], head, ...more });
const folder = (names) => ({ kind: "desk", folder: names.map((name) => ({ name })) });
const BRANCH = {
  ...ADD,
  command: "git branch <name>",
  picture: {
    frames: [
      { label: "Before", caption: "One name, main.", show: [chainOf("main"), folder(["notes.txt"])] },
      { label: "After", command: "git branch scout", caption: "A second tag.", show: [chainOf("main", { names: [{ name: "main", on: "plot", kind: "branch" }, { name: "scout", on: "plot", kind: "branch", fresh: true }] })], gloss: "HEAD is on main, not on scout." },
    ],
  },
  changed: "one name, scout",
  same: "no new commit",
  runs: [[{ command: "git branch", output: "* main\n  scout\n" }]],
  look: ["* main"],
};

test("a card's frames show their label, the command after it, their caption, pictures and a gloss, joined by an arrow", () => {
  const card = create(BRANCH);
  const frames = [...card.querySelectorAll(".gc-frame")];
  assert.equal(frames.length, 2);
  assert.equal(frames[1].querySelector(".gc-label").textContent, "After git branch scout");
  assert.equal(frames[1].querySelector(".gc-label code").textContent, "git branch scout");
  assert.match(frames[0].querySelector("figcaption").textContent, /One name, main\./);
  assert.ok(frames[0].querySelector(".gp-chain") && frames[0].querySelector(".gp-desk"));
  assert.equal(frames[1].querySelector(".gc-gloss").textContent, "HEAD is on main, not on scout.");
  assert.equal(card.querySelectorAll(".gc-frames .gc-then").length, 1);
});

test("what changed and what stayed the same are said in words under the frames", () => {
  const facts = [...create(BRANCH).querySelectorAll(".gc-facts li")].map((item) => item.textContent);
  assert.deepEqual(facts, ["Changed one name, scout", "Same no new commit"]);
});

test("a line git printed that matches the picture is marked to look at, in its own mark, not gold", () => {
  const terminal = create(BRANCH).querySelector(".gc-term");
  assert.deepEqual([...terminal.querySelectorAll(".gc-look")].map((node) => node.textContent), ["* main"]);
  assert.equal(terminal.textContent, "$ git branch\n* main\n  scout\n");
});

const REFUSED = [{ command: "git switch scout", output: "error: Your local changes would be overwritten\nAborting\n" }];
const SWITCH = {
  ...BRANCH,
  sections: [{
    title: "When you have edits you have not committed",
    between: "or",
    frames: [
      { label: "Comes along", caption: "The edit comes with you.", run: [{ command: "git switch scout", output: "M\tnotes.txt\n" }], look: ["M\tnotes.txt"] },
      { label: "Refused", caption: "git stops.", run: REFUSED, refused: ["Aborting"], stop: true, gloss: "\"stash\" sets edits aside." },
    ],
  }],
};

test("a folded section is closed until the reader opens it, and holds its own frames, each with its own terminal", () => {
  const section = create(SWITCH).querySelector("details.gc-section");
  assert.equal(section.hasAttribute("open"), false);
  assert.equal(section.querySelector("summary").textContent, "When you have edits you have not committed");
  assert.equal(section.querySelectorAll(".gc-frame .gc-term").length, 2);
});

test("outcomes are joined by \"or\", and a refusal is its own kind of frame, with git's refusal marked", () => {
  const section = create(SWITCH).querySelector(".gc-section");
  assert.equal(section.querySelector(".gc-frames .gc-or").textContent, "or");
  const refused = section.querySelectorAll(".gc-frame")[1];
  assert.ok(refused.classList.contains("is-refused"));
  assert.equal(refused.querySelector(".gc-refused").textContent, "Aborting");
});

test("a card with no transcript of its own leaves out What git prints", () => {
  assert.doesNotMatch(create({ ...SWITCH, runs: [] }).textContent, /What git prints/);
});

const GRAPH_RUN = [{ command: "git log --oneline --graph --all", output: "* 59039c2 (HEAD -> main) Plot the route\n* 3090621 Start the project\n" }];

test("a decoded graph puts git's lines beside the chain, one row for each line of output under the command", () => {
  const card = create({ ...BRANCH, picture: { frames: [{ label: "", caption: "Newest at the top.", decode: true, run: GRAPH_RUN, show: [chainOf("main")] }] } });
  const decoder = card.querySelector(".gc-decoder");
  const [typed, ...lines] = decoder.querySelectorAll(".gc-term .gc-line");
  assert.equal(typed.querySelector(".gc-typed").textContent, "git log --oneline --graph --all");
  assert.deepEqual(lines.map((line) => line.textContent), ["* 59039c2 (HEAD -> main) Plot the route", "* 3090621 Start the project"]);
  assert.equal(decoder.querySelectorAll(".chain-row").length, lines.length);
});

test("the message git prepares is shown as the editor would: its subject marked, git's comment lines after it", () => {
  const card = create({ ...BRANCH, picture: { frames: [{ label: "The message git prepares", caption: "", message: "Merge branch 'scout'\n# Please enter a commit message\n" }] } });
  const editor = card.querySelector(".gc-editor");
  assert.equal(editor.querySelector(".gc-look").textContent, "Merge branch 'scout'");
  assert.deepEqual([...editor.querySelectorAll(".gc-comment")].map((node) => node.textContent), ["# Please enter a commit message"]);
});

test("frames that hold a chain come with the line that says what HEAD and a dashed name are", () => {
  assert.match(create(BRANCH).textContent, /HEAD marks where you are/);
});

test("words can carry code and a commit's subject: code as code, the subject in italics", () => {
  const card = create({ ...BRANCH, changed: ["one name, ", { code: "scout" }, ", on ", { em: "Plot the route" }] });
  const changed = card.querySelector(".gc-fact.is-changed");
  assert.equal(changed.querySelector("code").textContent, "scout");
  assert.equal(changed.querySelector("em").textContent, "Plot the route");
  assert.equal(changed.textContent, "Changed one name, scout, on Plot the route");
});

test("a sum shows one command as the two it does at once", () => {
  const sum = [{ command: "git branch lights", says: "a new tag" }, { command: "git switch lights", says: "HEAD hops onto it" }, { command: "git switch -c lights", says: "both at once" }];
  const card = create({ ...BRANCH, sum });
  assert.equal(card.querySelector(".gc-sum").textContent, "git branch lightsa new tag+git switch lightsHEAD hops onto it=git switch -c lightsboth at once");
});

test("a key of git's drawing pairs each symbol with what it means", () => {
  const card = create({ ...BRANCH, glyphs: [["*", "a commit"], ["|", "a line down to the parent"]] });
  assert.deepEqual([...card.querySelectorAll(".gc-glyphs dt")].map((node) => node.textContent), ["*", "|"]);
  assert.deepEqual([...card.querySelectorAll(".gc-glyphs dd")].map((node) => node.textContent), ["a commit", "a line down to the parent"]);
});

test("a section that is the card's own content is not folded, and shows what git printed under its frames", () => {
  const card = create({ ...BRANCH, picture: undefined, runs: [], sections: [{ title: "Only scout moved on", fold: false, frames: BRANCH.picture.frames, run: [{ command: "git merge scout", output: "Fast-forward\n" }], look: ["Fast-forward"] }] });
  const section = card.querySelector(".gc-section");
  assert.equal(section.tagName, "SECTION");
  assert.equal(section.querySelector("h3").textContent, "Only scout moved on");
  assert.equal(section.querySelector(".gc-term .gc-look").textContent, "Fast-forward");
  assert.equal(card.querySelector(".gc-pictures"), null);
});
