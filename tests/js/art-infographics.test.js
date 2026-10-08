"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { html } = require("./fakedom");
const { installBrowser, load } = require("./load");
const { INFOGRAPHICS_STYLE, TOKENS, assertPalette, assertStyled, walk } = require("./art-check");

installBrowser();
const { ArtInfographics } = load(["dom.js", "art-pixels.js", "art-sprites.js", "art-infographics.js"], ["ArtInfographics"]);

const SOON = "Coming up in sector 5";

const COMMANDS = {
  title: "Every command, by what it does",
  groups: [
    {
      title: "Look around",
      commands: [
        { command: "git status", what: "Says which files are untracked, modified or staged.", tag: null },
        { command: "git log", what: "Lists the commits, newest first.", tag: SOON },
      ],
    },
    { title: "Undo", commands: [{ command: "git reflog", what: "Lists where HEAD has been.", tag: SOON }] },
  ],
};

const PLACES = {
  title: "Git's four places",
  places: [
    { id: "workshop", space: "Workshop", git: "working folder", what: "Your files as you edit them.", tag: null },
    { id: "dock", space: "Cargo dock", git: "staging area", what: "The files you chose for your next commit.", tag: null },
    { id: "vault", space: "Vault", git: "local repository", what: "Every commit you made.", tag: null },
    { id: "mothership", space: "Mothership", git: "remote repository", what: "A copy on a server.", tag: SOON },
  ],
  moves: [
    { from: "workshop", to: "dock", command: "git add", tag: null },
    { from: "dock", to: "workshop", command: "git restore --staged", tag: null },
    { from: "dock", to: "vault", command: "git commit", tag: null },
    { from: "vault", to: "workshop", command: "git switch, git restore", tag: SOON },
    { from: "vault", to: "mothership", command: "git push", tag: SOON },
    { from: "mothership", to: "workshop", command: "git pull (fetch, then merge)", tag: SOON },
  ],
};

const STATES = {
  title: "A file's states",
  states: [
    { id: "untracked", name: "untracked", space: "new in the workshop", what: "In no commit and not staged.", tag: null },
    { id: "staged", name: "staged", space: "on the dock", what: "Ready for the next commit.", tag: null },
    { id: "committed", name: "committed", space: "sealed in the vault", what: "Saved in a commit.", tag: null },
    { id: "modified", name: "modified", space: "edited in the workshop", what: "Changed since its last commit.", tag: SOON },
  ],
  moves: [
    { from: "untracked", to: "staged", how: "git add", tag: null },
    { from: "staged", to: "committed", how: "git commit", tag: null },
    { from: "committed", to: "modified", how: "edit the file", tag: SOON },
    { from: "modified", to: "committed", how: "git restore (drops the edit)", tag: SOON },
  ],
};

const textOf = (node) => node.textContent;
const heading = (node) => [...walk(node)].find((element) => element.localName === "h2");

function assertWell(node) {
  assertPalette(node);
  assertStyled(node);
  for (const picture of [...walk(node)].filter((element) => element.localName === "svg")) assert.equal(picture.getAttribute("aria-hidden"), "true", "pictures are decoration");
}

test("the command cards show every command and what it does, under its group", () => {
  const guide = ArtInfographics.commands(COMMANDS);
  assert.equal(heading(guide).textContent, COMMANDS.title);
  for (const group of COMMANDS.groups) assert.ok(textOf(guide).includes(group.title));
  const cards = [...guide.querySelectorAll(".art-ig-card")];
  assert.deepEqual(cards.map((card) => card.querySelector("code").textContent), ["git status", "git log", "git reflog"]);
  for (const [index, entry] of COMMANDS.groups.flatMap((group) => group.commands).entries()) assert.ok(textOf(cards[index]).includes(entry.what), entry.what);
  assertStyled(guide);
  assert.equal(guide.querySelectorAll("svg").length, 0, "the cards are words only");
});

test("a tagged command card is drawn in full, marked upcoming, with its tag as a badge", () => {
  const guide = ArtInfographics.commands(COMMANDS);
  const [status, log, reflog] = guide.querySelectorAll(".art-ig-card");
  assert.ok(!status.classList.contains("art-ig-card--upcoming"));
  assert.equal(status.querySelector(".art-ig-tag"), null);
  for (const card of [log, reflog]) {
    assert.ok(card.classList.contains("art-ig-card--upcoming"));
    assert.equal(card.querySelector(".art-ig-tag").textContent, SOON);
  }
  assert.equal(textOf(log), "git logLists the commits, newest first." + SOON);
  assertStyled(guide);
});

test("a tag is a non-empty string or null, and nothing else", () => {
  const card = (tag) => ({ ...COMMANDS, groups: [{ title: "x", commands: [{ command: "git status", what: "y", tag }] }] });
  for (const bad of [undefined, "", true, false]) assert.throws(() => ArtInfographics.commands(card(bad)), TypeError, String(bad));
  assert.throws(() => ArtInfographics.places({ ...PLACES, places: PLACES.places.map((place) => ({ ...place, tag: undefined })) }), TypeError);
  assert.throws(() => ArtInfographics.states({ ...STATES, moves: [{ from: "untracked", to: "staged", how: "git add" }] }), TypeError);
});

test("the four places show their space word, Git term and what, in their zone colours, with a picture each", () => {
  const guide = ArtInfographics.places(PLACES);
  assert.equal(heading(guide).textContent, PLACES.title);
  const boxes = [...guide.querySelectorAll(".art-ig-box")];
  assert.deepEqual(boxes.map((box) => box.getAttribute("style")), ["--tone:var(--z-wd)", "--tone:var(--z-st)", "--tone:var(--z-va)", "--tone:var(--z-re)"]);
  for (const place of PLACES.places) for (const words of [place.space, place.git, place.what]) assert.ok(textOf(guide).includes(words), words);
  assert.ok(boxes.every((box) => box.querySelector("svg")));
  assertWell(guide);
});

test("the moves between places are drawn arrows labelled with their command, forward above and back below", () => {
  const guide = ArtInfographics.places(PLACES);
  const moves = [...guide.querySelectorAll(".art-ig-move")];
  assert.equal(moves.length, PLACES.moves.length);
  assert.deepEqual(moves.map((move) => move.querySelector(".art-ig-move-label").textContent), PLACES.moves.map(({ command }) => command));
  assert.ok(moves.every((move) => move.querySelector(".art-ig-arrow svg")), "every arrow is drawn");
  const rowOf = (move) => Number(move.getAttribute("style").match(/grid-row:(\d+)/)[1]);
  const boxRow = Number(guide.querySelector(".art-ig-boxes").getAttribute("style").match(/grid-row:(\d+)/)[1]);
  moves.forEach((move, index) => {
    const forward = move.classList.contains("art-ig-move--forward");
    assert.equal(forward, [0, 2, 4].includes(index));
    assert.ok(forward ? rowOf(move) < boxRow : rowOf(move) > boxRow);
  });
});

test("an arrow spans from the middle of its first place to the middle of its last, and arrows in a row never overlap", () => {
  const guide = ArtInfographics.places(PLACES);
  const spans = [...guide.querySelectorAll(".art-ig-move")].map((move) => {
    const [, from, to, row] = move.getAttribute("style").match(/grid-column:(\d+) \/ (\d+);grid-row:(\d+)/).map(Number);
    return { from, to, row };
  });
  assert.deepEqual(spans.slice(0, 3).map(({ from, to }) => [from, to]), [[2, 4], [2, 4], [4, 6]]);
  assert.deepEqual([spans[5].from, spans[5].to], [2, 8]);
  for (const one of spans) for (const other of spans) if (one !== other && one.row === other.row) assert.ok(one.to <= other.from || other.to <= one.from);
});

test("tagged places and moves are drawn in full, dashed, with their tag as a badge", () => {
  const guide = ArtInfographics.places(PLACES);
  const upcoming = [...guide.querySelectorAll(".art-ig-box--upcoming")];
  assert.equal(upcoming.length, 1);
  for (const words of ["Mothership", "remote repository", "A copy on a server"]) assert.ok(textOf(upcoming[0]).includes(words), words);
  assert.equal(upcoming[0].querySelector(".art-ig-tag").textContent, SOON);
  assert.ok(upcoming[0].querySelector("svg"), "its picture is still drawn");
  const moves = [...guide.querySelectorAll(".art-ig-move--upcoming")];
  assert.deepEqual(moves.map((move) => move.querySelector(".art-ig-move-label").textContent), ["git switch, git restore", "git push", "git pull (fetch, then merge)"]);
  assert.ok(moves.every((move) => move.querySelector(".art-ig-tag").textContent === SOON));
  assert.equal(guide.querySelectorAll(".art-ig-tag").length, 4);
  assert.match(INFOGRAPHICS_STYLE, /\.art-ig-move--upcoming[^{]*\{[^}]*dashed/);
  assert.match(INFOGRAPHICS_STYLE, /\.art-ig-box--upcoming\s*\{[^}]*dashed/);
  assert.match(INFOGRAPHICS_STYLE, /\.art-ig-card--upcoming\s*\{[^}]*dashed/);
  assertWell(guide);
});

test("upcoming items never fade their words: only frames, shafts and pictures change", () => {
  for (const rule of INFOGRAPHICS_STYLE.matchAll(/([^{}]*--upcoming[^{]*)\{([^}]*)\}/g)) {
    const [, selector, body] = rule;
    if (/opacity/.test(body)) assert.match(selector, /art-ig-pic/, selector);
  }
});

test("every arrow names its two ends for screen readers, in the words of the places", () => {
  const guide = ArtInfographics.places(PLACES);
  const ends = [...guide.querySelectorAll(".art-ig-move")].map((move) => [...move.querySelectorAll(".art-ig-sr")].map(textOf));
  assert.deepEqual(ends[0], ["Workshop", "Cargo dock"]);
  assert.deepEqual(ends[4], ["Vault", "Mothership"]);
});

test("a tagged arrow reads as from, label, to, then its tag", () => {
  const guide = ArtInfographics.places(PLACES);
  const push = [...guide.querySelectorAll(".art-ig-move")][4];
  assert.equal(textOf(push), "Vaultgit pushMothership" + SOON);
});

test("the file's states show the Git name, the space words and what, with labelled arrows", () => {
  const guide = ArtInfographics.states(STATES);
  assert.equal(heading(guide).textContent, STATES.title);
  for (const state of STATES.states) for (const words of [state.name, state.space, state.what]) assert.ok(textOf(guide).includes(words), words);
  for (const move of STATES.moves) assert.ok(textOf(guide).includes(move.how), move.how);
  assert.equal(guide.querySelectorAll(".art-ig-box--upcoming").length, 1);
  assert.equal(guide.querySelectorAll(".art-ig-move--upcoming").length, 2);
  assert.deepEqual([...guide.querySelectorAll(".art-ig-box")].map((box) => box.getAttribute("style")), ["--tone:var(--s-new)", "--tone:var(--z-st)", "--tone:var(--z-va)", "--tone:var(--s-mod)"]);
  assertWell(guide);
});

test("an unknown place, state or move end is refused", () => {
  assert.throws(() => ArtInfographics.places({ ...PLACES, places: [{ ...PLACES.places[0], id: "moon" }], moves: [] }), RangeError);
  assert.throws(() => ArtInfographics.places({ ...PLACES, moves: [{ from: "workshop", to: "moon", command: "x", tag: null }] }), RangeError);
  assert.throws(() => ArtInfographics.states({ ...STATES, moves: [{ from: "staged", to: "staged", how: "x", tag: null }] }), RangeError);
});

test("each infographic is one element, drawn the same each time", () => {
  for (const [name, data] of [["commands", COMMANDS], ["places", PLACES], ["states", STATES]]) {
    const guide = ArtInfographics[name](data);
    assert.equal(guide.localName, "section");
    assert.ok(guide.classList.contains(`art-ig--${name}`));
    assert.equal(html(guide), html(ArtInfographics[name](data)));
  }
});

test("the infographics sheet paints only with design tokens, light and dark alike", () => {
  assert.doesNotMatch(INFOGRAPHICS_STYLE, /#[0-9a-fA-F]{3,6}\b/);
  for (const [, token] of INFOGRAPHICS_STYLE.matchAll(/var\((--[\w-]+)\)/g)) assert.ok(TOKENS.has(token) || ["--tone", "--columns", "--boxes", "--f-px", "--f-body", "--f-term"].includes(token), token);
  assert.doesNotMatch(INFOGRAPHICS_STYLE, /prefers-color-scheme/);
});

test("each infographic sits under the page's h1: its title an h2, its group and box names h3", () => {
  for (const guide of [ArtInfographics.commands(COMMANDS), ArtInfographics.places(PLACES), ArtInfographics.states(STATES)]) {
    const levels = (className) => [...guide.querySelectorAll(`.${className}`)].map((node) => node.localName);
    assert.deepEqual(levels("art-ig-title"), ["h2"]);
    const names = [...levels("art-ig-group-title"), ...levels("art-ig-name")];
    assert.ok(names.length > 0);
    assert.ok(names.every((level) => level === "h3"));
    assert.equal(guide.querySelectorAll("h4").length, 0);
  }
});
