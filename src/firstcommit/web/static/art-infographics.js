"use strict";

/*
 * The field guide's three infographics. Every word comes from the data passed in (the shape of
 * InfographicText, each `unlock` replaced by `locked: true|false`); this module adds only the
 * pictures, the arrows and the layout. A locked item shows `lockedLabel` and none of its own
 * words. Pictures are aria-hidden decoration; all words are real text. Defines one global,
 * ArtInfographics; dom.js, art-pixels.js and art-sprites.js load first, art-infographics.css
 * styles it.
 *
 * commands({title, groups: [{title, commands: [{command, what, locked}]}], lockedLabel})
 *     a grid of night command cards per group.
 * places({title, places: [{id, space, git, what, locked}], moves: [{from, to, command, locked}], lockedLabel})
 *     the four places (ids workshop, dock, vault, mothership) as zones in their colours.
 * states({title, states: [{id, name, space, what, locked}], moves: [{from, to, how, locked}], lockedLabel})
 *     a file's states (ids untracked, staged, committed, modified) as pixel boxes.
 *
 * In places and states the boxes stand in a row, in the data's order; each move is an arrow
 * labelled with its command, from the middle of one box to the middle of another, above the row
 * when it points right and below when it points left. Each returns one <section>.
 */

/* global Dom, ArtPixels, ArtSprites */
/* exported ArtInfographics */

const ArtInfographics = (function () {
  const { el } = Dom;
  const { tone, draw, picture, sprite } = ArtPixels;

  const PLACE_LOOKS = {
    workshop: { colour: "z-wd", art: () => sprite("file") },
    dock: { colour: "z-st", art: () => sprite("crate") },
    vault: { colour: "z-va", art: () => sprite("capsule") },
    mothership: { colour: "z-re", art: () => sprite("ship") },
  };
  const STATE_COLOURS = { untracked: "s-new", staged: "z-st", committed: "z-va", modified: "s-mod" };
  const stateArt = (id) => () => sprite("file", { p: tone(STATE_COLOURS[id]) });

  const ARROW_HEAD = ["k....", "kk...", "kkk..", "kkkk.", "kkkkk", "kkkk.", "kkk..", "kk...", "k...."];
  const PIXEL = 3;

  /* A sprite's <rect>s in an <svg> PIXEL screen pixels to the grid pixel. */
  function pixelPicture(rects, className) {
    const width = Math.max(...rects.map((rect) => Number(rect.getAttribute("x")) + Number(rect.getAttribute("width"))));
    const height = Math.max(...rects.map((rect) => Number(rect.getAttribute("y")) + 1));
    return picture({ class: className, viewBox: `0 0 ${width} ${height}`, width: width * PIXEL, height: height * PIXEL }, "", rects);
  }

  const heading = (title) => el("h3", { class: "art-ig-title" }, title);
  const lockNote = (lockedLabel) => el("p", { class: "art-ig-lock" }, ArtSprites.icon("lock"), lockedLabel);

  function commandCard({ command, what, locked }, lockedLabel) {
    if (locked) return el("li", { class: "art-ig-card art-ig-card--locked" }, lockNote(lockedLabel));
    return el("li", { class: "art-ig-card" }, el("code", { class: "art-ig-command" }, command), el("p", { class: "art-ig-what" }, what));
  }

  function commands({ title, groups, lockedLabel }) {
    return el("section", { class: "art-ig art-ig--commands" },
      heading(title),
      groups.map((group) => el("section", { class: "art-ig-group" },
        el("h4", { class: "art-ig-group-title" }, group.title),
        el("ul", { class: "art-ig-cards", role: "list" }, group.commands.map((entry) => commandCard(entry, lockedLabel))))));
  }

  /* One box of the row: {colour, art, name, term, what, locked}. */
  function box({ colour, art, name, term, what, locked }, lockedLabel) {
    const frame = { class: locked ? "art-ig-box art-ig-box--locked" : "art-ig-box", style: `--tone:${tone(colour)}` };
    const drawing = pixelPicture(art(), "art-ig-pic");
    if (locked) return el("div", frame, drawing, lockNote(lockedLabel));
    return el("div", frame,
      drawing,
      el("h4", { class: "art-ig-name" }, name),
      el("p", { class: "art-ig-term" }, term),
      el("p", { class: "art-ig-what" }, what));
  }

  function arrow() {
    const head = picture({ class: "art-ig-head", viewBox: "0 0 5 9", width: 10, height: 18 }, "", draw(ARROW_HEAD, { k: "currentColor" }));
    return el("span", { class: "art-ig-arrow", "aria-hidden": "true" }, el("span", { class: "art-ig-shaft" }), head);
  }

  /* Gives every move a row on its side of the boxes, shortest first, so arrows in one row never
     overlap: {move, forward, first, last, row}, `first` and `last` the grid lines of its ends. */
  function packRows(moves, indexOf) {
    const placed = moves.map((move) => {
      const from = indexOf(move.from);
      const to = indexOf(move.to);
      if (from === to) throw new RangeError(`a move needs two different ends, not ${move.from} twice`);
      return { move, forward: to > from, first: 2 * Math.min(from, to) + 2, last: 2 * Math.max(from, to) + 2, row: 0 };
    });
    const bySpan = [...placed].sort((one, other) => one.last - one.first - (other.last - other.first));
    for (const arrowPlace of bySpan) {
      const taken = (row) => placed.some((other) => other.row === row && other.forward === arrowPlace.forward && other.first < arrowPlace.last && arrowPlace.first < other.last);
      let row = 1;
      while (taken(row)) row += 1;
      arrowPlace.row = row;
    }
    return placed;
  }

  /* The row of boxes with labelled arrows: forward rows above (row 1 nearest), backward below. */
  function flow(kind, { title, boxes, moves, lockedLabel }) {
    const ids = boxes.map(({ id }) => id);
    const indexOf = (id) => {
      if (!ids.includes(id)) throw new RangeError(`no ${kind} ${id}`);
      return ids.indexOf(id);
    };
    const nameOf = (id) => {
      const end = boxes[indexOf(id)];
      return end.locked ? lockedLabel : end.name;
    };
    const placed = packRows(moves, indexOf);
    const above = Math.max(0, ...placed.filter(({ forward }) => forward).map(({ row }) => row));
    const gridRow = ({ forward, row }) => (forward ? above - row + 1 : above + 1 + row);
    return el("section", { class: `art-ig art-ig--${kind}` },
      heading(title),
      el("div", { class: "art-ig-flow", style: `--columns:${boxes.length * 2}` },
        el("div", { class: "art-ig-boxes", style: `grid-row:${above + 1};--boxes:${boxes.length}` }, boxes.map((entry) => box(entry, lockedLabel))),
        placed.map((arrowPlace) => {
          const { move, forward, first, last } = arrowPlace;
          const classes = ["art-ig-move", forward ? "art-ig-move--forward" : "art-ig-move--back", move.locked && "art-ig-move--locked"].filter(Boolean).join(" ");
          return el("div", { class: classes, style: `grid-column:${first} / ${last};grid-row:${gridRow(arrowPlace)}` },
            el("span", { class: "art-ig-sr" }, nameOf(move.from)),
            el("span", { class: "art-ig-move-label" }, move.locked ? lockedLabel : move.label),
            el("span", { class: "art-ig-sr" }, nameOf(move.to)),
            arrow());
        })));
  }

  function look(table, id, kind) {
    if (!(id in table)) throw new RangeError(`unknown ${kind}: ${id}`);
    return table[id];
  }

  function places({ title, places: entries, moves, lockedLabel }) {
    const boxes = entries.map(({ id, space, git, what, locked }) => ({ id, ...look(PLACE_LOOKS, id, "place"), name: space, term: git, what, locked }));
    return flow("places", { title, boxes, moves: moves.map((move) => ({ ...move, label: move.command })), lockedLabel });
  }

  function states({ title, states: entries, moves, lockedLabel }) {
    const boxes = entries.map(({ id, name, space, what, locked }) => ({ id, colour: look(STATE_COLOURS, id, "state"), art: stateArt(id), name, term: space, what, locked }));
    return flow("states", { title, boxes, moves: moves.map((move) => ({ ...move, label: move.how })), lockedLabel });
  }

  return { commands, places, states };
})();
