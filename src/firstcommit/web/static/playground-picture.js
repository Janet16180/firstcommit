"use strict";

/*
 * The playground's one picture (docs/drafts/playground/plan.md, "Views"): the view the player
 * picked, drawn live from each look at the playground's lab. Chain, Desk, Move log and Graph draw
 * one repository, yours or Alex's (`whose`); History and Crew always show both people. The views
 * are the levels' own pictures: chain.js (with a line naming the work in no commit yet), desk.js,
 * move-log.js, git-graph.js, zone-panel.js for History (the chart, stacked where the screen
 * stacks it) and Crew, and keep-panel.js for Conflict. Needs those and dom.js and strings.js.
 * Defines one global, PlaygroundPicture.
 *
 * MAIN, MORE              the views on the tab row, and those under More views, in order.
 * PER_PERSON              the views that draw one person's repository.
 * create(view, {stacked, timers, reducedMotion, onWrite, onType})
 *                         {element, refresh(now)}: `stacked` says whether History stacks its
 *                         sides; Conflict writes picks with onWrite({person, file, read, choices})
 *                         and types at a prompt with onType(person, line); now = {observation
 *                         (PlaygroundObservation), whose ("you" or "alex"), alexShown, reflogRead
 *                         (git reflog typed in that repository), editing ({you, alex}: the
 *                         editor each terminal runs, {editor, path}, or null)}.
 */

/* global Dom, Strings, Chain, Desk, MoveLog, GitGraph, ZonePanel, KeepPanel */
/* exported PlaygroundPicture */

const PlaygroundPicture = (function () {
  const { el } = Dom;
  const { t } = Strings;
  const MAIN = Object.freeze(["chain", "history", "desk", "crew", "conflict"]);
  const MORE = Object.freeze(["movelog", "graph"]);
  const PER_PERSON = Object.freeze(["chain", "desk", "movelog", "graph", "conflict"]);
  const CHANGES = { untracked: "new", modified: "edited", deleted: "deleted", typechange: "edited" };

  const other = (whose) => (whose === "alex" ? "you" : "alex");
  const tip = (snapshot, name) => (snapshot.refs.find((ref) => ref.name === name) || {}).target;

  /* The mothership's main is not where this repository's origin/main bookmark says. */
  const moved = (project, github) => Boolean(github) && tip(github, "main") !== tip(project, "origin/main");

  /* "In your folder, in no commit yet: notes.txt (modified)", in git's words, or nothing when all
     is committed. */
  function loose(project, whose) {
    const files = project.files.filter((file) => !file.ignored && (file.index_change || file.folder_change));
    const named = files.map((file) => `${file.path} (${t(`zones.tag.${file.folder_change ? CHANGES[file.folder_change] : "staged"}`)})`);
    return el("p", { class: "pg-loose", hidden: !named.length }, `${t(`pg.loose.${whose}`)} ${named.join(", ")}`);
  }

  const BUILD = {
    chain() {
      const chain = Chain.create();
      const line = el("div", {});
      return {
        elements: [chain.element, line],
        refresh({ observation, whose, alexShown, reflogRead }) {
          const me = observation[whose];
          const them = observation[other(whose)];
          chain.update({
            project: me.project,
            github: observation.github,
            teammate: them ? them.project : null,
            ghosts: me.ghosts,
            show: { mothership: alexShown || moved(me.project, observation.github), alex: alexShown, ghosts: reflogRead },
            look: [],
            walk: false,
            owner: whose,
          });
          line.replaceChildren(loose(me.project, whose));
        },
      };
    },

    desk() {
      const desk = Desk.create();
      return {
        elements: [desk.element],
        refresh({ observation, whose }) {
          const me = observation[whose];
          desk.update({ project: me.project, texts: me.texts, lines: me.texts.map((text) => text.path), kept: false, blink: false });
        },
      };
    },

    movelog() {
      const moveLog = MoveLog.create({ onPick: () => {} });
      return {
        elements: [moveLog.element],
        refresh({ observation, whose, reflogRead }) {
          const me = observation[whose];
          moveLog.update({ reflog: me.reflog, ghosts: me.ghosts, typed: reflogRead, marks: true });
        },
      };
    },

    graph() {
      const graph = GitGraph.create();
      return { elements: [graph.element], refresh: ({ observation, whose }) => graph.update(observation[whose].graph, []) };
    },

    history(options) {
      const zones = ZonePanel.create(options);
      zones.mode(options.stacked ? "stack" : "chart");
      return {
        elements: [zones.element],
        refresh: ({ observation }) => zones.update({ project: observation.you.project, github: observation.github, teammate: null, commands: observation.you.commands }),
      };
    },

    crew(options) {
      const zones = ZonePanel.create(options);
      return {
        elements: [zones.element],
        refresh: ({ observation }) => zones.update({ project: observation.you.project, github: observation.github, teammate: observation.alex ? observation.alex.project : null, commands: observation.you.commands }),
      };
    },

    conflict({ onWrite, onType }) {
      let person = "you";
      const keep = KeepPanel.create({ onWrite: (request) => onWrite({ person, ...request }), onType: (line) => onType(person, line) });
      return {
        elements: [keep.element],
        refresh({ observation, whose, editing }) {
          person = whose;
          keep.update({ person, markers: observation[whose].markers, texts: observation[whose].texts, editing: editing[whose] });
        },
      };
    },
  };

  function create(view, { stacked = false, timers = window, reducedMotion = true, onWrite = null, onType = null } = {}) {
    const built = BUILD[view]({ stacked, timers, reducedMotion, onWrite, onType });
    const element = el("div", { class: "pg-picture", "data-view": view }, built.elements);
    return { element, refresh: built.refresh };
  }

  return { MAIN, MORE, PER_PERSON, create };
})();
