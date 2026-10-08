"use strict";

/*
 * Dev mode's level list (#/dev): every sector with its levels, each with its number, title and
 * id, and a link straight to it, so a level can be opened without playing the ones before it.
 * Shown only when the game runs in dev mode (Status.dev); otherwise it says how to turn it on.
 * Needs dom.js, strings.js and progress.js. Defines one global, DevList.
 *
 * create(ctx) {element}: ctx.status() is the dashboard.
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

  function create(ctx) {
    const status = ctx.status();
    const body = status.dev ? status.chapters.map((chapter) => sector(status.chapters, chapter)) : [say("dev.off")];
    return { element: el("section", { class: "panel dev" }, el("h1", {}, t("dev.title")), body) };
  }

  return { create };
})();
