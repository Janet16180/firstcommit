"use strict";

/*
 * The chapters' cheat sheets (firstcommit/game.py's Notes), one chapter at a time, with every
 * chapter listed beside them. Needs dom.js, markup.js and progress.js. Defines one global,
 * NotesView.
 */

/* global Dom, Markup, Progress */
/* exported NotesView */

const NotesView = (function () {
  const { el } = Dom;

  /* The chapter to open without one in the address: the level in progress's, else the first with cards. */
  function defaultChapter(status) {
    const active = status.active && Progress.findLevel(status.chapters, status.active.level);
    const withCards = status.chapters.find((chapter) => chapter.cards > 0) || status.chapters[0];
    return active ? active.chapter.id : withCards.id;
  }

  async function fill(article, game, chapter) {
    try {
      const notes = await game.notes(chapter);
      article.replaceChildren(el("p", { class: "kicker" }, "Notes"), el("h1", {}, notes.title), el("div", { class: "prose" }, Markup.render(notes.notes)));
    } catch (error) {
      if (error.status !== 404) throw error;
      article.replaceChildren(el("h1", {}, "No notes for this chapter yet"), el("p", {}, "Its notes arrive with its first level."));
    }
  }

  /* ctx: game, status(). `chapter` is a chapter id, or null for the default one. */
  function create(ctx, chapter) {
    const status = ctx.status();
    const open = chapter || defaultChapter(status);
    const article = el("article", { class: "notes panel" }, el("p", { class: "loading" }, "Loading the notes…"));
    const element = el("div", { class: "notes-page" },
      el("nav", { class: "notes-nav", "aria-label": "Chapters" }, el("ol", {}, status.chapters.map((item) => el("li", {},
        item.levels.length > 0
          ? el("a", { href: `#/notes/${encodeURIComponent(item.id)}`, "aria-current": item.id === open ? "page" : null }, item.title)
          : el("span", { class: "is-soon" }, item.title, " ", el("span", { class: "coming-soon" }, "Coming soon")),
      )))),
      article,
    );
    fill(article, ctx.game, open);
    return { element };
  }

  return { create };
})();
