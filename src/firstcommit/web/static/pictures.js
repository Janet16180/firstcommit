"use strict";

/*
 * A level's teaching pictures (docs/drafts/teaching-pictures.md): at most two on screen, a large
 * one and a small one under it, chosen by the level (LevelView.pictures). The chain may carry the
 * folder row under it, the captain's chart beside it in a challenge, and git's own --graph
 * drawing once the game sends it. The pictures answer what the player types: `git log` lights the
 * chain's walk until the next lines, `git diff` makes the desk's red lines blink, and `git reflog`
 * fills the move log, after which the commits only it reaches appear on the chain. Picking a move
 * rings its commit on the chain. A level that reads a file as it was (spec.past) shows the past
 * panel beside the chain and rings the commit read; once a `git log` naming that file worked, it
 * dims the commits that did not change it (Observation.past.touched). spec.plain draws the
 * chain's capsules alone (sector 3, before the chain is born), and during spec.quiet's steps the
 * chain's legend is hidden. Needs dom.js, strings.js, chain.js, folder-row.js, desk.js,
 * move-log.js, target-chart.js, git-graph.js, sides.js and past-panel.js. Defines one global,
 * Pictures.
 *
 * create(spec, {challenge, target, timers}) {element, update(observation, {look, passed, step})}:
 *   spec is LevelView.pictures, target LevelView.target (the captain's chart, beside the chain); in a
 *   challenge the move log marks nothing. Once the step spec.whatif.after
 *   has passed, the chain plays its WHAT IF for as long as a what-if moment, timed on `timers`
 *   (window unless given), then rewinds. `look` lists what the current
 *   goal rings (subjects, or "HEAD"); `passed` the ids of the goals met, for the desk's outline;
 *   `step` the current step's id.
 */

/* global Dom, Chain, FolderRow, Desk, MoveLog, TargetChart, GitGraph, Sides, PastPanel */
/* exported Pictures */

const Pictures = (function () {
  const { el } = Dom;
  const WALK = /^git log\b(?!.*--all)/;
  const DIFF = /^git diff\b/;
  const REFLOG = /^git reflog\b/;
  /* As long as the what-if moments play. */
  const WHATIF_MS = 7000;

  /* The latest read of the level's file, and the commits git log said changed it (the others dim). */
  const readOf = (spec, observation) => (spec.past && observation.past ? observation.past.read : null);
  const touchedOf = (spec, observation, logged) => (spec.past && observation.past && logged ? observation.past.touched : null);
  /* A typed `git log` naming the level's file; the caller keeps only those that worked. */
  const logsFile = (line, path) => /^git log\b/.test(line) && line.split(/\s+/).includes(path);
  const ringed = (rings, read) => (read && read.subject ? [...rings, read.subject] : rings);

  /* Each picture: its elements in a slot, and how it redraws from a tick (`now`). */
  const BUILD = {
    chain(spec, { target }) {
      const chain = Chain.create();
      const folder = spec.folder ? FolderRow.create() : null;
      const chart = target ? TargetChart.create() : null;
      const graph = spec.graph ? GitGraph.create() : null;
      const past = spec.past ? PastPanel.create() : null;
      const side = chart || past;
      const beside = side || graph ? el("div", { class: side ? "pictures-pair" : "pictures-pair is-stack" }, chain.element, side && side.element) : null;
      return {
        elements: [beside || chain.element, folder && folder.element],
        refresh({ observation, rings, walking, ghosts, whatif, rewound, quiet, logged }) {
          const { project } = observation;
          const read = readOf(spec, observation);
          chain.update({
            project,
            github: observation.github,
            teammate: observation.teammate,
            ghosts: observation.ghosts,
            show: { mothership: spec.mothership, alex: spec.alex, ghosts },
            look: ringed(rings, read),
            walk: walking,
            whatif: whatif ? spec.whatif.without : null,
            plain: spec.plain,
            touched: touchedOf(spec, observation, logged),
            legend: !quiet,
          });
          if (past) past.update({ file: spec.past, past: read });
          chain.element.classList.toggle("is-rewind", rewound);
          if (folder) folder.update(project.files);
          if (chart) chart.update(project, target);
          if (!graph || !observation.graph) return;
          if (!graph.element.parentNode) beside.append(graph.element);
          graph.update(observation.graph, rings);
        },
      };
    },

    desk(spec) {
      const desk = Desk.create();
      return {
        elements: [desk.element],
        refresh: ({ observation, passed, blinking }) => desk.update({ project: observation.project, texts: observation.texts, lines: spec.lines, kept: spec.kept !== null && passed.includes(spec.kept), blink: blinking }),
      };
    },

    movelog(spec, { challenge, onPick }) {
      const moveLog = MoveLog.create({ onPick });
      return {
        elements: [moveLog.element],
        refresh: ({ observation, reflogRead }) => moveLog.update({ reflog: observation.reflog, ghosts: observation.ghosts, typed: reflogRead, marks: !challenge }),
      };
    },

    sides() {
      const sides = Sides.create();
      return { elements: [sides.element], refresh: ({ observation }) => sides.update(observation.conflicts) };
    },
  };

  function create(spec, { challenge = false, target = null, timers = window } = {}) {
    const state = { picked: null, walking: false, blinking: false, reflogRead: false, logged: false, whatif: "waiting", last: null };
    const options = { challenge, target, onPick: (hash) => repick(hash) };
    const large = BUILD[spec.large](spec, options);
    const small = spec.small ? BUILD[spec.small](spec, options) : null;
    const element = el("div", { class: "pictures" },
      el("div", { class: "pictures-large" }, large.elements),
      el("div", { class: "pictures-small" }, small ? small.elements : []));
    const hasMoveLog = spec.large === "movelog" || spec.small === "movelog";

    function draw() {
      const { observation, look, passed, step } = state.last;
      const picked = [...observation.project.commits, ...observation.ghosts].find((commit) => commit.hash === state.picked);
      const now = {
        observation,
        passed,
        rings: picked ? [...look, picked.subject] : look,
        walking: state.walking,
        blinking: state.blinking,
        reflogRead: state.reflogRead,
        ghosts: spec.ghosts && (!hasMoveLog || state.reflogRead),
        whatif: state.whatif === "playing",
        rewound: state.whatif === "rewound",
        quiet: spec.quiet.includes(step),
        logged: state.logged,
      };
      for (const picture of [large, small].filter(Boolean)) picture.refresh(now);
    }

    function repick(hash) {
      state.picked = hash;
      if (state.last) draw();
    }

    function update(observation, { look, passed, step = null }) {
      state.last = { observation, look, passed, step };
      const typed = observation.commands.map((command) => command.line.trim());
      if (typed.length) {
        state.walking = typed.some((line) => WALK.test(line));
        state.blinking = typed.some((line) => DIFF.test(line));
      }
      state.reflogRead = state.reflogRead || typed.some((line) => REFLOG.test(line));
      state.logged = state.logged || Boolean(spec.past && observation.commands.some((command) => command.status === 0 && logsFile(command.line.trim(), spec.past)));
      if (spec.whatif && state.whatif === "waiting" && passed.includes(spec.whatif.after)) playWhatIf();
      draw();
    }

    /* The WHAT IF plays once, then rewinds to the real chain. */
    function playWhatIf() {
      state.whatif = "playing";
      timers.setTimeout(() => {
        state.whatif = "rewound";
        draw();
      }, WHATIF_MS);
    }

    return { element, update };
  }

  return { create };
})();
