"use strict";

/*
 * The field guide, reached from the map: three infographics drawn by the artist
 * (art-infographics.js) from the words of infographic-text.js: Git's four places and the commands
 * between them, a file's states, and every command the game teaches. What the player has not
 * learned yet is locked: an item unlocks when enough levels of its chapter are done
 * (firstcommit/game.py's Status). Needs dom.js, art-sprites.js,
 * art-infographics.js and infographic-text.js. Defines one global, FieldGuide.
 */

/* global Dom, ArtSprites, ArtInfographics, InfographicText */
/* exported FieldGuide */

const FieldGuide = (function () {
  const { el } = Dom;

  /* Whether `unlock` ({chapter, levels}) is met in `status`: that many of the chapter's levels
     done, in any order, or all of them when `levels` is left out; a chapter with no levels yet
     unlocks nothing. */
  function unlocked(status, { chapter: id, levels }) {
    const chapter = status.chapters.find((item) => item.id === id);
    if (!chapter || chapter.levels.length === 0) return false;
    const done = chapter.levels.filter((level) => level.done).length;
    return done >= (levels ?? chapter.levels.length);
  }

  /* The items with their `unlock` replaced by `locked`, as the art takes them. */
  const lock = (status, list) => list.map(({ unlock, ...item }) => ({ ...item, locked: !unlocked(status, unlock) }));

  /* Boxes and the moves between them: a move stays locked while either of its boxes is. */
  function diagram(status, boxes, moves) {
    const shown = lock(status, boxes);
    const closed = new Set(shown.filter((box) => box.locked).map((box) => box.id));
    return { boxes: shown, moves: lock(status, moves).map((move) => ({ ...move, locked: move.locked || closed.has(move.from) || closed.has(move.to) })) };
  }

  function create(ctx) {
    const status = ctx.status();
    const { places, states, commands, locked } = InfographicText;
    const placeDiagram = diagram(status, places.places, places.moves);
    const stateDiagram = diagram(status, states.states, states.moves);
    const element = el("div", { class: "field-guide" },
      el("header", { class: "guide-head" },
        el("a", { class: "btn", href: "#/" }, ArtSprites.icon("back"), "Map"),
        el("div", {}, el("h1", {}, InfographicText.title), el("p", {}, InfographicText.lede)),
      ),
      ArtInfographics.places({ title: places.title, places: placeDiagram.boxes, moves: placeDiagram.moves, lockedLabel: locked }),
      ArtInfographics.states({ title: states.title, states: stateDiagram.boxes, moves: stateDiagram.moves, lockedLabel: locked }),
      ArtInfographics.commands({ title: commands.title, groups: commands.groups.map((group) => ({ title: group.title, commands: lock(status, group.commands) })), lockedLabel: locked }),
    );
    return { element };
  }

  return { create, unlocked };
})();
