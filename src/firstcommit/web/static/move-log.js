"use strict";

/*
 * The move log (docs/drafts/teaching-pictures.md, idea 8): HEAD's moves, one row per line of
 * `git reflog`, in git's order and exactly as git printed it (ReflogEntry.line), newest first.
 * It stays empty until the player types `git reflog`; then its rows light up one after another,
 * in step with the terminal's lines. A later move slides in at the top and every HEAD@{n} below
 * it grows by one. Picking a row names the commit it landed on (the chain rings it); the pick
 * stays on its move as newer rows push it down. A row whose commit no name leads to says so,
 * unless the level keeps quiet (a challenge). Needs dom.js and strings.js. Defines one global,
 * MoveLog.
 *
 * create({onPick}) {element, update({reflog, ghosts, typed, marks})}: the log, from
 *   Observation.reflog and Observation.ghosts; `typed` says whether git reflog was typed. An
 *   update that brings nothing new keeps the drawing.
 */

/* global Dom, Strings */
/* exported MoveLog */

const MoveLog = (function () {
  const { el } = Dom;
  const { t } = Strings;
  /* git's line with its HEAD@{n} picked out. */
  const pickedOut = (line) => {
    const [before, ref, after] = line.split(/(HEAD@\{\d+\})/);
    return ref ? [before, el("span", { class: "movelog-ref" }, ref), after] : [line];
  };

  function create({ onPick = () => {} } = {}) {
    const element = el("section", { class: "movelog", "aria-label": t("movelog.label") });
    let drawnFrom = null;
    let shown = null;
    /* The picked move, counted from the oldest, so it keeps its move as the log grows. */
    let picked = null;

    function draw({ reflog, ghosts, typed, marks }) {
      element.setAttribute("aria-label", t("movelog.label"));
      const head = el("h3", { class: "movelog-title" }, t("movelog.title"));
      if (!typed) {
        shown = null;
        element.replaceChildren(head, el("p", { class: "movelog-empty" }, Strings.parts("movelog.empty").map((part) => (typeof part === "string" ? part : el("code", {}, part.code)))));
        return;
      }
      const lighting = shown === null;
      const fresh = shown === null ? 0 : Math.max(0, reflog.length - shown);
      shown = reflog.length;
      const lost = new Set(ghosts.map((commit) => commit.hash));
      element.replaceChildren(head, el("ol", { class: "movelog-rows" }, ...reflog.map((move, at) => {
        const kinds = ["movelog-row", lighting && "is-lit", at < fresh && "is-fresh", picked === reflog.length - 1 - at && "is-picked"].filter(Boolean);
        const row = el("button", { type: "button", class: kinds.join(" "), "data-hash": move.new, "aria-pressed": String(picked === reflog.length - 1 - at), onclick: () => pick(reflog.length - 1 - at, move.new) },
          el("code", { class: "movelog-line" }, pickedOut(move.line)),
          marks && lost.has(move.new) && el("span", { class: "movelog-noname" }, t("movelog.noname")));
        if (lighting) row.style.setProperty("--step", String(at));
        return el("li", {}, row);
      })));
    }

    let last = null;

    /* A pick redraws the same rows, neither lit again nor fresh. */
    function pick(index, hash) {
      picked = index;
      onPick(hash);
      shown = last.reflog.length;
      draw(last);
    }

    function update(view) {
      const key = JSON.stringify([view, Strings.language()]);
      if (key === drawnFrom) return;
      drawnFrom = key;
      last = view;
      draw(view);
    }

    return { element, update };
  }

  return { create };
})();
