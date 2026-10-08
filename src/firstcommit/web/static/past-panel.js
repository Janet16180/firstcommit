"use strict";

/*
 * A file as it was (docs/drafts/past/plan.md): the panel beside the chain that shows exactly what
 * `git show <commit>:<file>` printed, titled with the commit it read, or that the commit has no
 * such file. Before anything is read it says how to fill it; a read always ends saying the folder
 * is not changed. Needs dom.js and strings.js. Defines one global, PastPanel.
 *
 * create() {element, update({file, past})}: file is the level's file (LevelView.pictures.past),
 *   past the latest read (Observation.past.read: {rev, commit, subject, text}), null before any.
 */

/* global Dom, Strings */
/* exported PastPanel */

const PastPanel = (function () {
  const { el } = Dom;
  const { t, parts } = Strings;
  const said = (key, params) => parts(key, params).map((part) => (typeof part === "string" ? part : el("code", {}, part.code)));

  function body(file, past) {
    if (!past) return ["empty", [el("p", { class: "past-empty" }, said("past.empty", { file }))]];
    if (!past.commit) return ["missing", [el("p", { class: "past-missing" }, said("past.unknown", { rev: past.rev }))]];
    if (past.text === null) return ["missing", [el("p", { class: "past-missing" }, said("past.missing", { file }))]];
    return ["read", [el("pre", { class: "past-text" }, past.text.replace(/\n$/, "")), el("p", { class: "past-note" }, t("past.note"))]];
  }

  function create() {
    const element = el("section", { class: "past", "aria-label": t("past.label") });
    return {
      element,

      update({ file, past }) {
        const [state, shown] = body(file, past);
        const title = past && past.subject ? t("past.title", { file, subject: past.subject }) : t("past.then", { file });
        element.dataset.state = state;
        element.replaceChildren(el("h3", { class: "past-title" }, title), ...shown);
      },
    };
  }

  return { create };
})();
