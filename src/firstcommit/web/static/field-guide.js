"use strict";

/*
 * The field guide, reached from the map: three infographics drawn by the artist
 * (art-infographics.js) from the words of infographic-text.js: Git's four places and the commands
 * between them, a file's states, and every command the game teaches. What the player has not
 * learned yet is locked: an item unlocks when the level that teaches it is done, or when every
 * level of its chapter is (firstcommit/game.py's Status). Needs dom.js, art-sprites.js,
 * art-infographics.js, progress.js and infographic-text.js. Defines one global, FieldGuide.
 */

/* global Dom, ArtSprites, ArtInfographics, Progress, InfographicText */
/* exported FieldGuide */

const FieldGuide = (function () {
  const { el } = Dom;

  /* Whether `unlock` ({level} or {chapter}) is met in `status`. */
  function unlocked(status, unlock) {
    let met = false;
    if (unlock.level) {
      const found = Progress.findLevel(status.chapters, unlock.level);
      met = Boolean(found && found.done);
    } else {
      const chapter = status.chapters.find((item) => item.id === unlock.chapter);
      met = Boolean(chapter && chapter.levels.length > 0 && chapter.levels.every((item) => item.done));
    }
    return met;
  }

  /* The items with their `unlock` replaced by `locked`, as the art takes them. */
  const lock = (status, list) => list.map(({ unlock, ...item }) => ({ ...item, locked: !unlocked(status, unlock) }));

  function create(ctx) {
    const status = ctx.status();
    const { places, states, commands, locked } = InfographicText;
    const element = el("div", { class: "field-guide" },
      el("header", { class: "guide-head" },
        el("a", { class: "btn", href: "#/" }, ArtSprites.icon("back"), "Map"),
        el("div", {}, el("h1", {}, InfographicText.title), el("p", {}, InfographicText.lede)),
      ),
      ArtInfographics.places({ title: places.title, places: lock(status, places.places), moves: lock(status, places.moves), lockedLabel: locked }),
      ArtInfographics.states({ title: states.title, states: lock(status, states.states), moves: lock(status, states.moves), lockedLabel: locked }),
      ArtInfographics.commands({ title: commands.title, groups: commands.groups.map((group) => ({ title: group.title, commands: lock(status, group.commands) })), lockedLabel: locked }),
    );
    return { element };
  }

  return { create, unlocked };
})();
