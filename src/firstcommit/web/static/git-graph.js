"use strict";

/*
 * Git's own drawing of the tree (docs/drafts/sector5/5-3, 5-4): the lines `git log --oneline
 * --graph --all` printed, beside the chain, so the player can match the two. The line of each
 * commit the chain rings (by subject) lights up with it. Needs dom.js and strings.js. Defines one
 * global, GitGraph.
 *
 * create() {element, update(lines, look)}: lines as Observation.graph gives them, look the
 *   subjects the chain rings.
 */

/* global Dom, Strings */
/* exported GitGraph */

const GitGraph = (function () {
  const { el } = Dom;

  function create() {
    const element = el("section", { class: "graph" });

    function update(lines, look) {
      const title = el("h4", { class: "graph-title" }, Strings.parts("graph.title").map((part) => (typeof part === "string" ? part : el("code", {}, part.code))));
      element.replaceChildren(title, el("pre", { class: "graph-lines" }, lines.map((line) => [
        el("span", { class: look.some((subject) => line.endsWith(` ${subject}`)) ? "graph-line is-look" : "graph-line" }, line), "\n"])));
    }

    return { element, update };
  }

  return { create };
})();
