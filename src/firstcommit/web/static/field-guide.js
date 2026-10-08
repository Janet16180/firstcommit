"use strict";

/*
 * The field guide, from the map or over a level: three infographics drawn by the artist
 * (art-infographics.js) from the words of infographic-text.js: Git's four places and the commands
 * between them, a file's states, and every command the game teaches. Everything is readable from
 * the start; what a sector still ahead teaches is tagged with that sector ("coming up in sector
 * 5", or "coming up later" for one the map does not list yet), so progress still shows. An item
 * is taught once enough levels of its chapter are done (firstcommit/game.py's Status). The words
 * are the page's language. Needs dom.js, strings.js, art-sprites.js, art-infographics.js and
 * infographic-text.js. Defines one global, FieldGuide.
 *
 * create(ctx, {onClose}) {element}: the guide for ctx.status(); with onClose, as an overlay over a
 *                       level, its head offers Close (which calls it) instead of the way to the map.
 * taught(status, taught) whether an item's lesson ({chapter, levels}) is done.
 */

/* global Dom, Strings, ArtSprites, ArtInfographics, InfographicText */
/* exported FieldGuide */

const FieldGuide = (function () {
  const { el } = Dom;

  /* Whether `taught` ({chapter, levels}) is met in `status`: that many of the chapter's levels
     done, in any order, or all of them when `levels` is left out; a chapter with no levels yet
     has taught nothing. */
  function taught(status, { chapter: id, levels }) {
    const chapter = status.chapters.find((item) => item.id === id);
    if (!chapter || chapter.levels.length === 0) return false;
    const done = chapter.levels.filter((level) => level.done).length;
    return done >= (levels ?? chapter.levels.length);
  }

  /* The text in one language: each {en, es} pair becomes its string in `language`. */
  function localized(value, language) {
    if (typeof value !== "object") return value;
    if (Array.isArray(value)) return value.map((item) => localized(item, language));
    if ("en" in value) return value[language];
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, localized(item, language)]));
  }

  /* The items with their `taught` replaced by `tag`: null once taught, else the sector ahead that teaches it. */
  function tagged(status, text, list) {
    return list.map(({ taught: lesson, ...item }) => {
      const sector = status.chapters.findIndex((chapter) => chapter.id === lesson.chapter) + 1;
      const ahead = sector ? text.upcoming.replace("{sector}", String(sector)) : text.later;
      return { ...item, tag: taught(status, lesson) ? null : ahead };
    });
  }

  function head(text, onClose) {
    const away = onClose
      ? el("button", { type: "button", class: "btn guide-close", onclick: onClose }, ArtSprites.icon("back"), Strings.t("guide.close"))
      : el("a", { class: "btn", href: "#/" }, ArtSprites.icon("back"), Strings.t("guide.map"));
    return el("header", { class: "guide-head" }, away, el("div", {}, el("h1", {}, text.title), el("p", {}, text.lede)));
  }

  function create(ctx, { onClose = null } = {}) {
    const status = ctx.status();
    const text = localized(InfographicText, Strings.language());
    const { places, states, commands } = text;
    const tag = (list) => tagged(status, text, list);
    const element = el("div", { class: "field-guide" },
      head(text, onClose),
      ArtInfographics.places({ title: places.title, places: tag(places.places), moves: tag(places.moves) }),
      ArtInfographics.states({ title: states.title, states: tag(states.states), moves: tag(states.moves) }),
      ArtInfographics.commands({ title: commands.title, groups: commands.groups.map((group) => ({ title: group.title, commands: tag(group.commands) })) }),
    );
    return { element };
  }

  return { create, taught };
})();
