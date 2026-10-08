"use strict";

/*
 * Dev mode's level list (#/dev): every sector with its levels, each with its number, title and
 * id, and a link straight to it, so a level can be opened without playing the ones before it.
 * Shown only when the game runs in dev mode (Status.dev); otherwise it says how to turn it on.
 * Under the sectors, the playground's starting points, each a link that opens it there.
 * Needs dom.js, strings.js and progress.js. Defines one global, DevList.
 *
 * create(ctx) {element}: ctx.status() is the dashboard, ctx.game the API.
 */

/* global Dom, Strings, Progress */
/* exported DevList */

const DevList = (function () {
  const { el } = Dom;
  const { t, parts } = Strings;

  const say = (key) => el("p", {}, parts(key).map((part) => (typeof part === "string" ? part : el("code", {}, part.code))));

  function level(chapters, summary) {
    const number = Progress.missionNumber(chapters, summary.id).number;
    return el("li", { class: "dev-level" },
      el("a", { href: `#/level/${encodeURIComponent(summary.id)}` }, el("span", { class: "dev-num" }, number), " ", summary.title),
      " ", el("code", {}, summary.id));
  }

  function sector(chapters, chapter) {
    return el("section", { class: "dev-sector" },
      el("h2", {}, chapter.title),
      chapter.levels.length ? el("ol", { class: "dev-levels" }, chapter.levels.map((summary) => level(chapters, summary))) : el("p", { class: "dev-none" }, t("dev.none")));
  }

  /* The playground's starting points, each a link that opens it there, once the game names them. */
  async function playground(ctx, section) {
    const { starts } = await ctx.game.playground();
    section.append(el("ol", { class: "dev-levels" }, starts.map((start) => el("li", { class: "dev-level" },
      el("a", { href: `#/playground?start=${encodeURIComponent(start.id)}` }, start.title), " ", el("code", {}, start.id)))));
  }

  function create(ctx) {
    const status = ctx.status();
    const starts = status.dev ? el("section", { class: "dev-playground" }, el("h2", {}, t("pg.title"))) : null;
    const body = status.dev ? [...status.chapters.map((chapter) => sector(status.chapters, chapter)), starts] : [say("dev.off")];
    if (starts) playground(ctx, starts);
    return { element: el("section", { class: "panel dev" }, el("h1", {}, t("dev.title")), body) };
  }

  return { create };
})();
