"use strict";

/*
 * Two sides (V5 in docs/drafts/chapters-5-9.md): each conflicted file opened like a book, your
 * half and the other person's side by side, each named with the branch it came from and showing
 * that side's version of the file, line by line, and what the file held before both under them.
 * It reads the observation's conflicts (git's index stages, so it stays true while the player
 * edits the file) and hides every other file on purpose. Needs dom.js and strings.js. Defines
 * one global, Sides.
 *
 * create() {element, update(conflicts)}: the stage, redrawn from Observation.conflicts.
 */

/* global Dom, Strings */
/* exported Sides */

const Sides = (function () {
  const { el } = Dom;
  const { t } = Strings;

  const lines = (list) => el("ol", { class: "sides-lines" }, list.map((line) => el("li", { class: "sides-line" }, line)));

  /* One half: who wrote it (you, or the other side's author by name), its branch and its lines. */
  function half(side, which) {
    const who = which === "you" ? t("sides.you") : side.author || side.label;
    return el("section", { class: "sides-half", "data-side": which, "data-author": which === "you" ? "you" : who.split(" ")[0].toLowerCase() },
      el("header", { class: "sides-head" }, el("b", { class: "sides-who" }, who), side.label && el("code", { class: "sides-branch" }, side.label)),
      side.lines === null ? el("p", { class: "sides-deleted" }, t("sides.deleted")) : lines(side.lines));
  }

  const book = (conflict) => el("article", { class: "sides-book" },
    el("h3", { class: "sides-path" }, conflict.path),
    el("div", { class: "sides-pages" }, half(conflict.you, "you"), half(conflict.them, "them")),
    conflict.base && el("div", { class: "sides-base" }, el("span", { class: "sides-base-name" }, t("sides.base")), lines(conflict.base)));

  function create() {
    const element = el("div", { class: "sides", role: "group", "aria-label": t("views.tab.sides") });
    return {
      element,

      update(conflicts) {
        element.replaceChildren(...(conflicts.length ? conflicts.map(book) : [el("p", { class: "sides-none" }, t("sides.none"))]));
      },
    };
  }

  return { create };
})();
