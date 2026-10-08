"use strict";

/*
 * The field guide's three infographics. Every word comes from the data passed in (the shape of
 * InfographicText, each `unlock` replaced by `tag`); this module adds only the pictures, the
 * arrows and the layout. Nothing is ever hidden: every item is drawn in full. An item whose `tag`
 * is a string (the page's localized words, e.g. "Coming up in sector 5") also shows that string
 * as a small quiet badge (.art-ig-tag) and carries the --upcoming modifier (.art-ig-card--upcoming,
 * .art-ig-box--upcoming, .art-ig-move--upcoming), slightly muted with its words fully readable.
 * `tag` must be a non-empty string or null; anything else throws a TypeError. Pictures are
 * aria-hidden decoration; all words are real text. Defines one global, ArtInfographics; dom.js
 * and art-pixels.js load first, art-infographics.css styles it.
 *
 * commands({title, groups: [{title, commands: [{command, what, tag}]}]})
 *     a grid of night command cards per group.
 * places({title, places: [{id, space, git, what, tag}], moves: [{from, to, command, tag}]})
 *     the four places (ids workshop, dock, vault, mothership) as zones in their colours.
 * states({title, states: [{id, name, space, what, tag}], moves: [{from, to, how, tag}]})
 *     a file's states (ids untracked, staged, committed, modified) as pixel boxes.
 *
 * In places and states the boxes stand in a row, in the data's order; each move is an arrow
 * labelled with its command, from the middle of one box to the middle of another, above the row
 * when it points right and below when it points left. A tagged move shows its tag beside its
 * label, on the side away from the arrow; screen readers hear "from, label, to, tag". Each
 * returns one <section>.
 */

/* global Dom, ArtPixels */
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

  const heading = (title) => el("h2", { class: "art-ig-title" }, title);

  function checkTag(tag) {
    if (tag === null || (typeof tag === "string" && tag !== "")) return tag;
    throw new TypeError(`a tag is a non-empty string or null, not ${JSON.stringify(tag)}`);
  }

  /* The item's classes, with its --upcoming modifier when tagged, and its badge (or nothing). */
  const classesOf = (base, tag) => (checkTag(tag) === null ? base : `${base} ${base}--upcoming`);
  const badge = (tag) => (tag === null ? [] : el("span", { class: "art-ig-tag" }, tag));

  function commandCard({ command, what, tag }) {
    return el("li", { class: classesOf("art-ig-card", tag) },
      el("code", { class: "art-ig-command" }, command),
      el("p", { class: "art-ig-what" }, what),
      badge(tag));
  }

  function commands({ title, groups }) {
    return el("section", { class: "art-ig art-ig--commands" },
      heading(title),
      groups.map((group) => el("section", { class: "art-ig-group" },
        el("h3", { class: "art-ig-group-title" }, group.title),
        el("ul", { class: "art-ig-cards", role: "list" }, group.commands.map(commandCard)))));
  }

  /* One box of the row: {colour, art, name, term, what, tag}. */
  function box({ colour, art, name, term, what, tag }) {
    return el("div", { class: classesOf("art-ig-box", tag), style: `--tone:${tone(colour)}` },
      pixelPicture(art(), "art-ig-pic"),
      el("h3", { class: "art-ig-name" }, name),
      el("p", { class: "art-ig-term" }, term),
      el("p", { class: "art-ig-what" }, what),
      badge(tag));
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
  function flow(kind, { title, boxes, moves }) {
    const ids = boxes.map(({ id }) => id);
    const indexOf = (id) => {
      if (!ids.includes(id)) throw new RangeError(`no ${kind} ${id}`);
      return ids.indexOf(id);
    };
    const nameOf = (id) => boxes[indexOf(id)].name;
    const placed = packRows(moves, indexOf);
    const above = Math.max(0, ...placed.filter(({ forward }) => forward).map(({ row }) => row));
    const gridRow = ({ forward, row }) => (forward ? above - row + 1 : above + 1 + row);
    return el("section", { class: `art-ig art-ig--${kind}` },
      heading(title),
      el("div", { class: "art-ig-flow", style: `--columns:${boxes.length * 2}` },
        el("div", { class: "art-ig-boxes", style: `grid-row:${above + 1};--boxes:${boxes.length}` }, boxes.map(box)),
        placed.map((arrowPlace) => {
          const { move, forward, first, last } = arrowPlace;
          const classes = `${classesOf("art-ig-move", move.tag)} art-ig-move--${forward ? "forward" : "back"}`;
          return el("div", { class: classes, style: `grid-column:${first} / ${last};grid-row:${gridRow(arrowPlace)}` },
            el("span", { class: "art-ig-move-text" },
              el("span", { class: "art-ig-sr" }, nameOf(move.from)),
              el("span", { class: "art-ig-move-label" }, move.label),
              el("span", { class: "art-ig-sr" }, nameOf(move.to)),
              badge(move.tag)),
            arrow());
        })));
  }

  function look(table, id, kind) {
    if (!(id in table)) throw new RangeError(`unknown ${kind}: ${id}`);
    return table[id];
  }

  function places({ title, places: entries, moves }) {
    const boxes = entries.map(({ id, space, git, what, tag }) => ({ id, ...look(PLACE_LOOKS, id, "place"), name: space, term: git, what, tag }));
    return flow("places", { title, boxes, moves: moves.map((move) => ({ ...move, label: move.command })) });
  }

  function states({ title, states: entries, moves }) {
    const boxes = entries.map(({ id, name, space, what, tag }) => ({ id, colour: look(STATE_COLOURS, id, "state"), art: stateArt(id), name, term: space, what, tag }));
    return flow("states", { title, boxes, moves: moves.map((move) => ({ ...move, label: move.how })) });
  }

  return { commands, places, states };
})();
