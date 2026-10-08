"use strict";

/*
 * The desk (docs/drafts/teaching-pictures.md, idea 7, and sector8/8-1): your working folder, the
 * staging area and your commits. Each file in the folder is tagged by where Git's copy of it is;
 * a drawn file shows its lines, and a line Git has no copy of (in the folder, not in the staging
 * area's copy) is red, "only here". Once the level says so, a dashed outline "Git has a copy"
 * rounds the staging area and the commits, and the red lines stay outside it. `git diff` makes
 * them blink; a restore dissolves them, shown once as gone. Needs dom.js and strings.js. Defines
 * one global, Desk.
 *
 * create() {element, update({project, texts, lines, kept, blink})}: project is a snapshot,
 *   texts Observation.texts ({path, folder, index}), lines the paths whose lines are drawn. An
 *   update that brings nothing new keeps the drawing.
 */

/* global Dom, Strings */
/* exported Desk */

const Desk = (function () {
  const { el } = Dom;
  const { t } = Strings;

  function statusOf(file) {
    let status = "saved";
    if (file.head === null && file.index === null) status = "new";
    else if (file.index !== file.head) status = file.folder === file.index ? "staged" : "stagedEdited";
    else if (file.folder !== file.index) status = "edited";
    return status;
  }

  const split = (text) => (text || "").split("\n").filter(Boolean);

  function create() {
    const element = el("section", { class: "desk", "aria-label": t("desk.label") });
    /* Per drawn file: its folder text and red lines last time, and the lines a change took away. */
    const before = new Map();

    function linesOf(text, blink) {
      const kept = new Set(split(text.index));
      const red = split(text.folder).filter((line) => !kept.has(line));
      const last = before.get(text.path);
      let gone = last ? last.gone : [];
      if (last && last.folder !== text.folder) gone = last.red.filter((line) => !split(text.folder).includes(line));
      before.set(text.path, { folder: text.folder, red, gone });
      const line = (words, kind) => el("span", { class: kind ? `desk-line ${kind}` : "desk-line" },
        el("span", { class: "desk-text" }, words),
        kind.startsWith("is-only") && el("span", { class: "desk-only" }, t("desk.only")));
      return [
        ...split(text.folder).map((words) => line(words, red.includes(words) ? `is-only${blink ? " is-blink" : ""}` : "")),
        ...gone.map((words) => line(words, "is-gone")),
      ];
    }

    let drawnFrom = null;

    function update(view) {
      const key = JSON.stringify([view, Strings.language()]);
      if (key === drawnFrom) return;
      drawnFrom = key;
      draw(view);
    }

    function draw({ project, texts, lines, kept, blink }) {
      const files = project.files.filter((file) => file.folder !== null && !file.ignored);
      const staged = project.files.filter((file) => statusOf(file).startsWith("staged"));
      const drawn = new Map(texts.filter((text) => lines.includes(text.path)).map((text) => [text.path, text]));
      const card = (file) => {
        const status = statusOf(file);
        return el("div", { class: "desk-file" },
          el("span", { class: "desk-name" }, file.path),
          status !== "saved" && el("span", { class: "desk-tag" }, t(`desk.tag.${status}`)),
          drawn.has(file.path) && linesOf(drawn.get(file.path), blink));
      };
      const zone = (kind, title, ...children) => el("div", { class: `desk-zone is-${kind}` }, el("h3", {}, title), ...children);
      element.setAttribute("aria-label", t("desk.label"));
      element.replaceChildren(
        zone("folder", t("desk.folder"), files.map(card)),
        el("div", { class: kept ? "desk-kept is-on" : "desk-kept" },
          kept && el("span", { class: "desk-kept-name" }, t("desk.kept")),
          zone("staging", t("desk.staging"), staged.length
            ? staged.map((file) => el("div", { class: "desk-file" }, el("span", { class: "desk-name" }, file.path), el("span", { class: "desk-tag" }, t("desk.tag.ready"))))
            : el("p", { class: "desk-empty" }, t("desk.empty"))),
          zone("commits", t("desk.commits"), project.commits.map((commit) => el("div", { class: "desk-commit" },
            el("span", { class: "desk-cap", "aria-hidden": "true" }),
            el("span", { class: "desk-subject" }, commit.subject),
            commit.hash === project.head && el("span", { class: "desk-head" }, "HEAD ▶ ", el("span", { class: "chain-tag is-head" }, project.branch || commit.short)))))));
    }

    return { element, update };
  }

  return { create };
})();
