"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, record } = require("./load");

const document = installBrowser();
const { makeEvent } = require("./fakedom");
const { FieldGuide, Strings } = load(["dom.js", "strings.js", "places.js", "chain.js", "art-pixels.js", "art-sprites.js", "art-infographics.js", "infographic-text.js", "guide-git.js", "guide-text.js", "guide-pictures.js", "guide-card.js", "guide-conflict.js", "field-guide.js"], ["FieldGuide", "Strings"]);

const level = (id, done) => ({ ...record("status").chapters[1].levels[0], id, title: id, done });
const status = (chapters) => ({ ...record("status"), chapters });
const two = (firstDone, secondDone) => status([{ id: "liftoff", title: "Lift-off", blurb: "", cards: 0, levels: [level("liftoff-aboard", firstDone), level("liftoff-flag", secondDone)] }, { id: "vault", title: "Vault", blurb: "", cards: 0, levels: [] }]);

test("an item is taught once enough of its chapter's levels are done, in any order", () => {
  assert.equal(FieldGuide.taught(two(false, true), { chapter: "liftoff", levels: 1 }), true);
  assert.equal(FieldGuide.taught(two(false, true), { chapter: "liftoff", levels: 2 }), false);
  assert.equal(FieldGuide.taught(two(true, true), { chapter: "liftoff", levels: 2 }), true);
});

test("a whole chapter is taught once every one of its levels is done; a chapter with none yet has taught nothing", () => {
  assert.equal(FieldGuide.taught(two(true, false), { chapter: "liftoff" }), false);
  assert.equal(FieldGuide.taught(two(true, true), { chapter: "liftoff" }), true);
  assert.equal(FieldGuide.taught(two(true, true), { chapter: "vault" }), false);
  assert.equal(FieldGuide.taught(two(true, true), { chapter: "nowhere" }), false);
});

test("the guide shows the four places, a file's states and every command, under a head with the way back to the map", () => {
  const view = FieldGuide.create({ status: () => two(true, false) });
  document.body.replaceChildren(view.element);
  assert.equal(view.element.querySelector("h1").textContent, "Field guide");
  assert.ok(view.element.querySelector('a[href="#/"]'));
  const titles = [...view.element.querySelectorAll(".art-ig-title")].map((node) => node.textContent);
  assert.deepEqual(titles, ["Git's four places", "A file's states", "Every command, by what it does", "When a merge stops: a conflict"]);
});

test("everything is readable from the start, nothing locked", () => {
  const view = FieldGuide.create({ status: () => two(false, false) });
  const text = view.element.textContent;
  assert.match(text, /git status/);
  assert.match(text, /Makes the current folder a repository/);
  assert.match(text, /a file the last commit holds/);
  assert.doesNotMatch(text, /Not learned yet/);
  assert.equal(view.element.querySelector(".art-ig-lock"), null);
});

test("what a sector still ahead teaches is tagged with that sector; what is taught carries no tag", () => {
  const view = FieldGuide.create({ status: () => two(true, false) });
  const tags = [...view.element.querySelectorAll(".art-ig-tag")].map((node) => node.textContent);
  assert.ok(tags.includes("Coming up in sector 1"));
  assert.ok(tags.includes("Coming up in sector 2"));
  const card = [...view.element.querySelectorAll(".art-ig-card")].find((node) => /git status/.test(node.textContent));
  assert.equal(card.querySelector(".art-ig-tag"), null);
});

test("a sector the map does not list yet is coming up later", () => {
  const view = FieldGuide.create({ status: () => two(true, true) });
  const tags = [...view.element.querySelectorAll(".art-ig-tag")].map((node) => node.textContent);
  assert.ok(tags.includes("Coming up later"));
});

test("a move is tagged by what teaches it alone, whatever its ends", () => {
  const view = FieldGuide.create({ status: () => status([{ id: "cargo", title: "Cargo", blurb: "", cards: 0, levels: [level("one", true), level("two", true)] }]) });
  const states = view.element.querySelector(".art-ig--states");
  assert.match(states.textContent, /a file the last commit holds/);
  const tagged = [...states.querySelectorAll(".art-ig-move")].filter((node) => node.classList.contains("art-ig-move--upcoming")).length;
  assert.ok(tagged < states.querySelectorAll(".art-ig-move").length);
});

test("opened over a level, the guide's head offers to close it instead of the way to the map", () => {
  let closed = 0;
  const view = FieldGuide.create({ status: () => two(true, false) }, { onClose: () => (closed += 1) });
  assert.equal(view.element.querySelector('a[href="#/"]'), null);
  view.element.querySelector(".guide-close").click();
  assert.equal(closed, 1);
});

test("the guide speaks the page's language", () => {
  Strings.use("es");
  try {
    const view = FieldGuide.create({ status: () => two(true, false) });
    assert.equal(view.element.querySelector("h1").textContent, "Guía de campo");
    assert.match(view.element.querySelector('a[href="#/"]').textContent, /Mapa/);
    assert.match(view.element.textContent, /\(taller\)/);
    assert.match(view.element.textContent, /Llega en el sector 2/);
    assert.doesNotMatch(view.element.textContent, /Workshop/);
  } finally {
    Strings.use("en");
  }
});

test("each place shows its real Git name first, with the game's name in parentheses", () => {
  const view = FieldGuide.create({ status: () => two(true, false) });
  const boxes = [...view.element.querySelectorAll(".art-ig--places .art-ig-box")];
  assert.deepEqual(boxes.map((box) => `${box.querySelector(".art-ig-name").textContent} ${box.querySelector(".art-ig-term").textContent}`), ["Working folder (workshop)", "Staging area (cargo dock)", "Repository (vault)", "Remote (mothership)"]);
});

const commandButton = (view, command) => [...view.element.querySelectorAll(".art-ig-open")].find((node) => node.querySelector("code").textContent === command);
const openCard = (view, command) => {
  document.body.replaceChildren(view.element);
  commandButton(view, command).click();
  return view.element.querySelector("dialog.guide-card-dialog");
};

test("clicking a command opens its card in a dialog, and closing it gives the focus back to the command", () => {
  const view = FieldGuide.create({ status: () => two(true, false) });
  const dialog = openCard(view, "git merge <branch>");
  assert.ok(dialog.open);
  assert.equal(dialog.querySelector(".gc-command").textContent, "git merge <branch>");
  assert.match(dialog.textContent, /Merge made by the 'ort' strategy\./);
  dialog.querySelector(".guide-card-close").click();
  assert.ok(!dialog.open);
  assert.equal(document.activeElement, commandButton(view, "git merge <branch>"));
});

test("a related command swaps the card in the same dialog", () => {
  const view = FieldGuide.create({ status: () => two(true, false) });
  const dialog = openCard(view, "git add <file>");
  const related = [...dialog.querySelectorAll(".gc-related button")].find((node) => node.textContent === "git status");
  related.click();
  assert.equal(view.element.querySelectorAll("dialog.guide-card-dialog").length, 1);
  assert.equal(dialog.querySelector(".gc-command").textContent, "git status");
});

test("a card says where the game teaches the command: its sector, mission and title, its sector, or a sector still to come", () => {
  const cargo = { id: "cargo", title: "Cargo", blurb: "", cards: 0, levels: [{ ...level("one", false), command: "git add" }, { ...level("two", false), title: "Stowaway", command: "git restore --staged" }] };
  const view = FieldGuide.create({ status: () => status([{ id: "liftoff", title: "Lift-off", blurb: "", cards: 0, levels: [] }, cargo]) });
  assert.match(openCard(view, "git restore --staged <file>").textContent, /Sector 2, mission 2: Stowaway/);
  assert.match(openCard(view, ".gitignore").textContent, /Sector 2: Cargo/);
  assert.match(openCard(view, "git reflog").textContent, /A sector still to come/);
});

test("Escape in a card closes the card only, not a guide opened over a level", () => {
  const view = FieldGuide.create({ status: () => two(true, false) }, { onClose: () => assert.fail("the guide closed") });
  const dialog = openCard(view, "git status");
  const cancel = makeEvent("cancel");
  dialog.dispatchEvent(cancel);
  assert.ok(cancel.stopped);
});

test("a merge's card leads to the conflict section and closes itself", () => {
  const view = FieldGuide.create({ status: () => two(true, false) });
  const dialog = openCard(view, "git merge <branch>");
  dialog.querySelector(".gc-conflict").click();
  assert.ok(!dialog.open);
  assert.equal(document.activeElement, view.element.querySelector("#guide-conflict"));
});

test("cards and the conflict speak the page's language", () => {
  Strings.use("es");
  try {
    const view = FieldGuide.create({ status: () => two(true, false) });
    assert.match(view.element.querySelector(".art-ig--places").textContent, /Carpeta de trabajo\(taller\)/);
    assert.match(openCard(view, "git add <file>").textContent, /Error común/);
    assert.match(view.element.querySelector(".guide-conflict").textContent, /Paso 1 de 7/);
  } finally {
    Strings.use("en");
  }
});

test("a jump bar leads to each part of the guide", () => {
  const view = FieldGuide.create({ status: () => two(true, false) });
  document.body.replaceChildren(view.element);
  const buttons = [...view.element.querySelectorAll(".guide-jump button")];
  assert.deepEqual(buttons.map((button) => button.textContent), ["Places", "File states", "Commands", "Conflict"]);
  buttons[2].click();
  assert.equal(document.activeElement, view.element.querySelector(".art-ig--commands"));
  buttons[3].click();
  assert.equal(document.activeElement, view.element.querySelector("#guide-conflict"));
});

test("a card opened in the guide links to its playground start", () => {
  const view = FieldGuide.create({ status: () => two(true, false) });
  const link = openCard(view, "git switch <branch>").querySelector("a.gc-try");
  assert.equal(link.getAttribute("href"), "#/playground?start=branches&view=chain&try=git%20switch%20bright-lights");
});

test("a card's frames and sections show the transcripts they name, and the merge's message as git prepared it", () => {
  const view = FieldGuide.create({ status: () => two(true, false) });
  const merge = openCard(view, "git merge <branch>");
  const sections = [...merge.querySelectorAll(".gc-section")];
  assert.match(sections[0].querySelector(".gc-term").textContent, /Fast-forward/);
  assert.match(sections[1].querySelector(".gc-term").textContent, /Merge made by the 'ort' strategy\./);
  assert.match(merge.querySelector(".gc-editor").textContent, /^\.git\/MERGE_MSGMerge branch 'scout'\n# Please enter a commit message/);
  const graph = openCard(view, "git log --oneline --graph --all");
  assert.equal(graph.querySelector(".gc-decoder .gc-typed").textContent, "git log --oneline --graph --all");
});

test("the branch cards' own words come in the page's language, git's words never", () => {
  Strings.use("es");
  try {
    const view = FieldGuide.create({ status: () => two(true, false) });
    const card = openCard(view, "git branch <name>");
    assert.match(card.textContent, /HEAD está en main, no en scout\./);
    assert.match(card.querySelector(".gc-term").textContent, /\(HEAD -> main, scout\) Plot the route/);
    assert.equal(card.querySelector(".gc-fact.is-changed em").textContent, "Plot the route");
  } finally {
    Strings.use("en");
  }
});
