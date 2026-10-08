"use strict";

/*
 * The black box's tape (V6 in docs/drafts/chapters-5-9.md): HEAD's moves as its reflog records
 * them, oldest to newest, one tick per move named by its kind (commit, reset, switch...) and the
 * capsule it landed on. A move to a capsule that only the reflog still reaches is a ghost. The
 * player scrubs the tape by clicking a tick or with the arrow keys; the readout names the chosen
 * move as git does (HEAD@{n}), in git's own words, which never change with the page's language.
 * Unsaved lines never make a tick. Needs dom.js and strings.js. Defines one global, Tape.
 *
 * create() {element, update(reflog, ghosts)}: the tape, redrawn from Observation.reflog (newest
 *          first) and Observation.ghosts. A move the player chose stays chosen as the tape grows;
 *          otherwise the newest is.
 */

/* global Dom, Strings */
/* exported Tape */

const Tape = (function () {
  const { el } = Dom;
  const { t } = Strings;
  const SHORT = 7;
  /* git's reflog messages start with the command that moved HEAD; a few name the same kind. */
  const KINDS = { commit: "commit", reset: "reset", checkout: "switch", switch: "switch", merge: "merge", pull: "pull", rebase: "rebase", "cherry-pick": "commit", revert: "commit", clone: "clone", branch: "branch" };

  const kindOf = (message) => KINDS[message.split(/[:( ]/)[0]] || "other";

  function create() {
    const track = el("div", { class: "tape-track", role: "listbox", "aria-label": t("tape.label") });
    const readout = el("div", { class: "tape-read", "aria-live": "polite" });
    const element = el("section", { class: "tape", "aria-label": t("tape.label") }, track, readout);
    let moves = [];
    let ghosts = new Set();
    /* The chosen move, counted from the oldest, or null to follow the newest. */
    let picked = null;

    const chosen = () => (picked === null ? moves.length - 1 : picked);

    function read() {
      const index = chosen();
      const move = moves[index];
      const ghost = ghosts.has(move.new);
      const parts = [
        el("code", { class: "tape-ref" }, `HEAD@{${moves.length - 1 - index}}`),
        el("span", { class: "tape-message" }, move.message),
        el("code", { class: "tape-at" }, move.new.slice(0, SHORT)),
        ghost && el("p", { class: "tape-ghost" }, t("tape.ghost")),
      ];
      readout.replaceChildren(...parts.filter(Boolean));
    }

    function choose(index) {
      picked = index;
      draw();
    }

    function draw() {
      if (!moves.length) {
        track.replaceChildren(el("p", { class: "tape-none" }, t("tape.none")));
        readout.replaceChildren();
        return;
      }
      const index = chosen();
      track.replaceChildren(...moves.map((move, at) => {
        const kind = kindOf(move.message);
        return el("button", { type: "button", role: "option", class: ghosts.has(move.new) ? "tape-tick is-ghost" : "tape-tick", "data-kind": kind, "aria-selected": String(at === index), tabindex: at === index ? "0" : "-1", onclick: () => choose(at) },
          el("span", { class: "tape-kind" }, t(`tape.kind.${kind}`)),
          el("code", { class: "tape-hash" }, move.new.slice(0, SHORT)));
      }));
      read();
    }

    track.addEventListener("keydown", (event) => {
      const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
      if (!step || !moves.length) return;
      choose(Math.min(moves.length - 1, Math.max(0, chosen() + step)));
    });

    return {
      element,

      update(reflog, ghostCommits) {
        moves = [...reflog].reverse();
        ghosts = new Set(ghostCommits.map((commit) => commit.hash));
        if (picked !== null && picked >= moves.length) picked = null;
        draw();
      },
    };
  }

  return { create };
})();
