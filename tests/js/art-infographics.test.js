"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { html } = require("./fakedom");
const { installBrowser, load } = require("./load");
const { INFOGRAPHICS_STYLE, TOKENS, assertPalette, assertStyled, walk } = require("./art-check");

installBrowser();
const { ArtInfographics } = load(["dom.js", "art-pixels.js", "art-sprites.js", "art-infographics.js"], ["ArtInfographics"]);

const LOCKED = "Not learned yet";

const COMMANDS = {
  title: "Every command, by what it does",
  lockedLabel: LOCKED,
  groups: [
    {
      title: "Look around",
      commands: [
        { command: "git status", what: "Says which files are untracked, modified or staged.", locked: false },
        { command: "git log", what: "Lists the commits, newest first.", locked: true },
      ],
    },
    { title: "Undo", commands: [{ command: "git reflog", what: "Lists where HEAD has been.", locked: true }] },
  ],
};

const PLACES = {
  title: "Git's four places",
  lockedLabel: LOCKED,
  places: [
    { id: "workshop", space: "Workshop", git: "working folder", what: "Your files as you edit them.", locked: false },
    { id: "dock", space: "Cargo dock", git: "staging area", what: "The files you chose for your next commit.", locked: false },
    { id: "vault", space: "Vault", git: "local repository", what: "Every commit you made.", locked: false },
    { id: "mothership", space: "Mothership", git: "remote repository", what: "A copy on a server.", locked: true },
  ],
  moves: [
    { from: "workshop", to: "dock", command: "git add", locked: false },
    { from: "dock", to: "workshop", command: "git restore --staged", locked: false },
    { from: "dock", to: "vault", command: "git commit", locked: false },
    { from: "vault", to: "workshop", command: "git switch, git restore", locked: true },
    { from: "vault", to: "mothership", command: "git push", locked: true },
    { from: "mothership", to: "workshop", command: "git pull (fetch, then merge)", locked: true },
  ],
};

const STATES = {
  title: "A file's states",
  lockedLabel: LOCKED,
  states: [
    { id: "untracked", name: "untracked", space: "new in the workshop", what: "In no commit and not staged.", locked: false },
    { id: "staged", name: "staged", space: "on the dock", what: "Ready for the next commit.", locked: false },
    { id: "committed", name: "committed", space: "sealed in the vault", what: "Saved in a commit.", locked: false },
    { id: "modified", name: "modified", space: "edited in the workshop", what: "Changed since its last commit.", locked: true },
  ],
  moves: [
    { from: "untracked", to: "staged", how: "git add", locked: false },
    { from: "staged", to: "committed", how: "git commit", locked: false },
    { from: "committed", to: "modified", how: "edit the file", locked: true },
    { from: "modified", to: "committed", how: "git restore (drops the edit)", locked: true },
  ],
};

const textOf = (node) => node.textContent;
const heading = (node) => [...walk(node)].find((element) => element.localName === "h3");

function assertWell(node) {
  assertPalette(node);
  assertStyled(node);
  for (const picture of [...walk(node)].filter((element) => element.localName === "svg")) assert.equal(picture.getAttribute("aria-hidden"), "true", "pictures are decoration");
}

test("the command cards show every unlocked command and what it does, under its group", () => {
  const guide = ArtInfographics.commands(COMMANDS);
  assert.equal(heading(guide).textContent, COMMANDS.title);
  for (const group of COMMANDS.groups) assert.ok(textOf(guide).includes(group.title));
  const status = guide.querySelector(".art-ig-card");
  assert.equal(status.querySelector("code").textContent, "git status");
  assert.ok(textOf(status).includes(COMMANDS.groups[0].commands[0].what));
  assertWell(guide);
});

test("a locked command card hides its command and text and shows a lock and the locked label", () => {
  const guide = ArtInfographics.commands(COMMANDS);
  const locked = guide.querySelectorAll(".art-ig-card--locked");
  assert.equal(locked.length, 2);
  for (const card of locked) {
    assert.equal(textOf(card), LOCKED);
    assert.ok(card.querySelector(".art-icon--lock"));
  }
  for (const hidden of ["git log", "Lists the commits", "git reflog", "where HEAD has been"]) assert.ok(!textOf(guide).includes(hidden), hidden);
});

test("the four places show their space word, Git term and what, in their zone colours, with a picture each", () => {
  const guide = ArtInfographics.places(PLACES);
  assert.equal(heading(guide).textContent, PLACES.title);
  const boxes = [...guide.querySelectorAll(".art-ig-box")];
  assert.deepEqual(boxes.map((box) => box.getAttribute("style")), ["--tone:var(--z-wd)", "--tone:var(--z-st)", "--tone:var(--z-va)", "--tone:var(--z-re)"]);
  for (const place of PLACES.places.filter(({ locked }) => !locked)) for (const words of [place.space, place.git, place.what]) assert.ok(textOf(guide).includes(words), words);
  assert.ok(boxes.every((box) => box.querySelector("svg")));
  assertWell(guide);
});

test("the moves between places are drawn arrows labelled with their command, forward above and back below", () => {
  const guide = ArtInfographics.places(PLACES);
  const moves = [...guide.querySelectorAll(".art-ig-move")];
  assert.equal(moves.length, PLACES.moves.length);
  assert.deepEqual(moves.map((move) => move.querySelector(".art-ig-move-label").textContent), ["git add", "git restore --staged", "git commit", LOCKED, LOCKED, LOCKED]);
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

test("locked places and moves are dimmed, dashed and show only the locked label", () => {
  const guide = ArtInfographics.places(PLACES);
  const mothership = guide.querySelector(".art-ig-box--locked");
  assert.ok(textOf(mothership).includes(LOCKED));
  for (const hidden of ["Mothership", "remote repository", "A copy on a server", "git push", "git pull", "git switch"]) assert.ok(!textOf(guide).includes(hidden), hidden);
  assert.equal(guide.querySelectorAll(".art-ig-move--locked").length, 3);
  assert.match(INFOGRAPHICS_STYLE, /\.art-ig-move--locked[^{]*\{[^}]*dashed/);
  assert.match(INFOGRAPHICS_STYLE, /\.art-ig-box--locked\s*\{[^}]*dashed/);
});

test("every arrow names its two ends for screen readers, in the words of the places", () => {
  const guide = ArtInfographics.places(PLACES);
  const ends = [...guide.querySelectorAll(".art-ig-move")].map((move) => [...move.querySelectorAll(".art-ig-sr")].map(textOf));
  assert.deepEqual(ends[0], ["Workshop", "Cargo dock"]);
  assert.deepEqual(ends[4], ["Vault", LOCKED]);
});

test("the file's states show the Git name, the space words and what, with labelled arrows", () => {
  const guide = ArtInfographics.states(STATES);
  assert.equal(heading(guide).textContent, STATES.title);
  for (const state of STATES.states.filter(({ locked }) => !locked)) for (const words of [state.name, state.space, state.what]) assert.ok(textOf(guide).includes(words), words);
  for (const move of STATES.moves.filter(({ locked }) => !locked)) assert.ok(textOf(guide).includes(move.how), move.how);
  for (const hidden of ["edited in the workshop", "Changed since", "edit the file", "drops the edit"]) assert.ok(!textOf(guide).includes(hidden), hidden);
  assert.deepEqual([...guide.querySelectorAll(".art-ig-box")].map((box) => box.getAttribute("style")), ["--tone:var(--s-new)", "--tone:var(--z-st)", "--tone:var(--z-va)", "--tone:var(--s-mod)"]);
  assertWell(guide);
});

test("an unknown place, state or move end is refused", () => {
  assert.throws(() => ArtInfographics.places({ ...PLACES, places: [{ ...PLACES.places[0], id: "moon" }], moves: [] }), RangeError);
  assert.throws(() => ArtInfographics.places({ ...PLACES, moves: [{ from: "workshop", to: "moon", command: "x", locked: false }] }), RangeError);
  assert.throws(() => ArtInfographics.states({ ...STATES, moves: [{ from: "staged", to: "staged", how: "x", locked: false }] }), RangeError);
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
