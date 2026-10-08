"use strict";

/*
 * The field guide's merge conflict, step by step: the "Markers decoded" prototype
 * (.scratch/conflict-poc/src/markers.html) on one real conflict GuideGit captured. The file git
 * wrote, markers and all; pointing at, tapping or focusing a line says whose it is, and leaving
 * puts the step's picture back. Then the player keeps your side, Alex's or both (a click, Enter
 * or Space on a side, or the buttons), sees the clean file, and git add and git commit make the
 * merge commit with two parents. You are violet, Alex green, the markers the conflict red; every
 * coloured line also carries its words. Every word arrives localized (GuideText.conflict); git's
 * own output and the file stay as git wrote them. Needs dom.js and guide-card.js (its terminal);
 * guide.css styles it. Defines one global, GuideConflict.
 *
 * create(git, words) {element}: git is GuideGit (its conflict and the conflict-* transcripts).
 */

/* global Dom, GuideCard */
/* exported GuideConflict */

const GuideConflict = (function () {
  const { el, svg } = Dom;
  const lines = (text) => text.replace(/\n$/, "").split("\n");
  const fill = (text, values) => text.replace(/\{(\w+)\}/g, (match, key) => (key in values ? values[key] : match));
  const MARKERS = new Set(["ours-start", "fence", "theirs-end"]);

  /* Each step: its stage (reading the markers, choosing, git add, git commit), what it lights in
     the marked file, and what the side panel explains when nothing is pointed at. */
  const STEPS = [
    { stage: "read", lit: ["ours-start", "ours", "fence", "theirs", "theirs-end"], frame: true, say: "wrote" },
    { stage: "read", lit: ["ours-start", "ours"], say: "ours-start" },
    { stage: "read", lit: ["fence", "theirs", "theirs-end"], say: "theirs-end" },
    { stage: "read", lit: ["clean-you", "clean-alex"], say: "clean-you" },
    { stage: "choose" },
    { stage: "add" },
    { stage: "commit" },
  ];

  /* The conflict's sides as lines, and the line where both changed the base. */
  function sidesOf(conflict) {
    const sides = { base: lines(conflict.base), ours: lines(conflict.ours), theirs: lines(conflict.theirs) };
    sides.clashAt = sides.base.findIndex((text, at) => sides.ours[at] !== text && sides.theirs[at] !== text);
    return sides;
  }

  /* Where a line of a resolved file came from: "you" or "alex" for a change Git merged on its
     own, "chosen" for a line from the conflict block, null for a line nobody changed. */
  function lineOrigin(text, { base, ours, theirs, clashAt }) {
    if (base.includes(text)) return null;
    if (ours.includes(text) && !theirs.includes(text) && text !== ours[clashAt]) return "you";
    if (theirs.includes(text) && !ours.includes(text) && text !== theirs[clashAt]) return "alex";
    return "chosen";
  }

  /* Each line of the marked file with the part it belongs to, read from the markers. */
  function parse(markers, sides) {
    let part = "clean";
    return lines(markers).map((text) => {
      let tag = part;
      if (text.startsWith("<<<<<<< ")) [tag, part] = ["ours-start", "ours"];
      else if (text === "=======") [tag, part] = ["fence", "theirs"];
      else if (text.startsWith(">>>>>>> ")) [tag, part] = ["theirs-end", "clean"];
      return { text, part: tag, from: tag === "clean" ? lineOrigin(text, sides) : null };
    });
  }

  const keyOf = (line) => (line.part === "clean" ? (line.from ? `clean-${line.from}` : "clean") : line.part);
  const note = (text, who) => el("span", { class: `gx-note gx-note--${who}` }, text);

  /* The words beside a line of the marked file: a side to pick says whether it is kept; a lit
     line says whose it is; anything else says nothing. */
  function noteFor(line, { on, pick, kept }, words) {
    const ours = line.part === "ours";
    if (pick) return note(kept ? words.keep.kept : ours ? words.keep.pickYours : words.keep.pickTheirs, ours ? "you" : "alex");
    if (!on) return null;
    if (ours) return note(words.who.you, "you");
    if (line.part === "theirs") return note(words.who.alex, "alex");
    if (line.from) return note(line.from === "you" ? words.who.youMerged : words.who.alexMerged, line.from);
    return null;
  }

  function legend(words) {
    const row = (code, kind, text) => el("div", {}, el("code", { class: `gx-mark gx-mark--${kind}` }, code), el("span", {}, text));
    return el("div", { class: "gx-legend" },
      row("<<<<<<< HEAD", "you", words.legend.start),
      row("=======", "fence", words.legend.fence),
      row(">>>>>>> alex-route", "alex", words.legend.end));
  }

  function editor(state, ok, list) {
    return el("div", { class: "gx-editor" },
      el("div", { class: "gx-editor-head" }, el("span", {}, "checklist.txt"), el("span", { class: ok ? "gx-state gx-state--ok" : "gx-state" }, state)),
      list);
  }

  /* The file once the markers are gone: the captured resolution for `choice`, or a prompt. */
  function cleanFile(conflict, sides, choice, words) {
    const list = el("ol", { class: "gx-file gx-file--clean", "aria-label": words.file.resolved });
    if (!choice) return el("div", {}, list, el("p", { class: "gx-empty" }, words.keep.none));
    list.append(...lines(conflict.resolved[choice]).map((text) => {
      const from = lineOrigin(text, sides);
      if (from === "chosen") return el("li", { class: "kept" }, text, note(text === sides.ours[sides.clashAt] ? words.file.keptYours : words.file.keptTheirs, "gold"));
      if (from) return el("li", { class: "merged", "data-from": from }, text, note(words.file.merged, "merged"));
      return el("li", {}, text);
    }));
    return list;
  }

  /* The buttons that keep a side: set(ours, theirs) keeps those. */
  function keepBox(choice, set, words) {
    const button = (label, name, ours, theirs) => el("button", {
      type: "button", class: "btn", "aria-pressed": name === null ? null : String(choice === name), onclick: () => set(ours, theirs),
    }, label);
    return el("div", { class: "gx-keep" },
      el("h3", {}, words.keep.title),
      el("p", { class: "gx-hint" }, words.keep.hint),
      el("div", { class: "gx-keep-buttons" },
        button(words.keep.yours, "yours", true, false),
        button(words.keep.theirs, "theirs", false, true),
        button(words.keep.both, "both", true, true),
        button(words.keep.reset, null, false, false)),
      choice === "both" ? el("p", { class: "gx-warn" }, words.keep.both2) : null,
      el("p", { class: "gx-hint" }, words.keep.byHand));
  }

  function capsule(x, y, who, hash) {
    return [
      svg("rect", { class: `gx-capsule gx-capsule--${who}`, x: x - 43, y: y - 17, width: 86, height: 34 }),
      svg("text", { class: "gx-hash", x, y: y + 6, "text-anchor": "middle" }, hash),
    ];
  }

  /* The merge as a diamond: where you both started, one commit each, and the merge commit on
     top with one parent line in each person's colour. */
  function diamond(conflict, choice, words) {
    const [merge, first, second] = conflict.head[choice].split(" ");
    const label = (x, y, who, text) => svg("text", { class: `gx-label gx-label--${who}`, x, y, "text-anchor": "middle" }, text);
    return el("div", { class: "gx-diamond-wrap" }, svg("svg", {
      class: "gx-diamond", viewBox: "0 0 400 290", role: "img", "aria-label": fill(words.diamond.label, { merge, first, second }),
    },
    svg("path", { class: "gx-wire gx-wire--base", d: "M200 250 L75 170 M200 250 L325 170" }),
    svg("path", { class: "gx-wire gx-wire--you", d: "M75 170 L200 60" }),
    svg("path", { class: "gx-wire gx-wire--alex", d: "M325 170 L200 60" }),
    capsule(200, 250, "base", conflict.baseCommit),
    capsule(75, 170, "you", conflict.yourCommit),
    capsule(325, 170, "alex", conflict.alexCommit),
    capsule(200, 60, "merge", merge),
    label(200, 22, "top", words.diamond.top),
    label(75, 210, "you", words.diamond.first),
    label(325, 210, "alex", words.diamond.second),
    label(200, 284, "base", words.diamond.base)));
  }

  /* One line of the marked file. While choosing, a side is a toggle button (toggle(part));
     otherwise every line can be pointed at, tapped or focused (point(line)). */
  function markedLine(line, { choosing, frame, kept, toggle, point }, words) {
    if (choosing && (line.part === "ours" || line.part === "theirs")) {
      const side = line.part === "ours" ? words.keep.yourSide : words.keep.alexSide;
      return el("li", {
        tabindex: "0", role: "button", class: "pick", "data-part": line.part, "aria-pressed": String(kept),
        "aria-label": fill(words.keep.pickLabel, { line: line.text, side }),
        onclick: () => toggle(line.part),
        onkeydown: (event) => {
          if (event.key !== "Enter" && event.key !== " ") return;
          event.preventDefault();
          toggle(line.part);
        },
      }, line.text);
    }
    const classes = [MARKERS.has(line.part) ? "marker" : "", frame && line.part !== "clean" ? "frame" : ""].join(" ").trim();
    const listen = (handler) => (choosing ? null : handler);
    return el("li", {
      tabindex: choosing ? null : "0", class: classes || null, "data-part": line.part, "data-from": line.from,
      onpointerenter: listen((event) => event.pointerType !== "touch" && point(line)),
      onpointerdown: listen(() => point(line)),
      onfocus: listen(() => point(line)),
    }, line.text);
  }

  /* The story's Back and Next, with the step's sentence: render(step) draws a step, and Next
     waits while canLeave(step) is false. refresh() redraws the step after a choice. */
  function story(words, canLeave, render) {
    let step = 0;
    const count = el("span", { class: "gx-count" });
    const sentence = el("p", { class: "gx-sentence", "aria-live": "polite" });
    const back = el("button", { type: "button", class: "btn gx-back", onclick: () => go(-1) }, words.back);
    const next = el("button", { type: "button", class: "btn primary gx-next", onclick: () => go(1) }, words.next);

    function refresh() {
      count.textContent = fill(words.count, { step: step + 1, steps: STEPS.length });
      sentence.textContent = words.steps[step];
      back.disabled = step === 0;
      next.disabled = step === STEPS.length - 1 || !canLeave(step);
      render(step);
    }

    function go(delta) {
      const target = step + delta;
      if (target < 0 || target >= STEPS.length || (delta > 0 && !canLeave(step))) return;
      step = target;
      refresh();
    }

    const element = el("nav", { class: "gx-story", "aria-label": words.title }, count, sentence, el("div", { class: "gx-buttons" }, back, next));
    return { element, refresh };
  }

  function create(git, words) {
    const { conflict } = git;
    const sides = sidesOf(conflict);
    const raw = parse(conflict.markers, sides);
    const commits = { yourCommit: conflict.yourCommit, alexCommit: conflict.alexCommit };
    const keep = { ours: false, theirs: false };
    const outcome = () => (keep.ours && keep.theirs ? "both" : keep.ours ? "yours" : keep.theirs ? "theirs" : null);
    const state = { step: 0, hover: null, items: [] };

    const left = el("div", { class: "gx-column" });
    const right = el("div", { class: "gx-column" });
    const terminal = (...runs) => GuideCard.terminal(runs.map((name) => git.runs[name]), words.silent);

    function explainBox() {
      const key = state.hover || STEPS[state.step].say;
      return el("div", { class: `gx-explain gx-explain--${key}` },
        el("h3", {}, words.parts[key].title),
        el("p", {}, fill(words.parts[key].text, commits)),
        el("p", { class: "gx-hint" }, words.hint));
    }

    /* Lights the marked file for the step and what is pointed at, in place, so leaving a line
       always puts the file back as the step drew it. */
    function paint() {
      const plan = STEPS[state.step];
      const lit = state.hover ? [state.hover] : plan.lit || [];
      for (const { li, line } of state.items) {
        const on = lit.includes(keyOf(line));
        const pick = li.classList.contains("pick");
        li.classList.toggle("on", on);
        li.classList.toggle("dim", lit.length > 0 && !on && !pick);
        li.querySelector(".gx-note")?.remove();
        const said = noteFor(line, { on, pick, kept: keep[line.part] }, words);
        if (said) li.append(said);
      }
      if (plan.stage === "read") right.replaceChildren(explainBox(), legend(words));
    }

    function setHover(key) {
      if (state.hover === key) return;
      state.hover = key;
      paint();
    }

    function markedFile() {
      const choosing = STEPS[state.step].stage === "choose";
      const toggle = (side) => {
        keep[side] = !keep[side];
        show();
      };
      const point = (line) => setHover(keyOf(line));
      state.items = raw.map((line) => ({ li: markedLine(line, { choosing, frame: STEPS[state.step].frame, kept: keep[line.part], toggle, point }, words), line }));
      return el("ol", {
        class: "gx-file gx-file--marked", "aria-label": words.file.withMarkers,
        onpointerleave: (event) => event.pointerType !== "touch" && setHover(null),
        onfocusout: (event) => !event.currentTarget.contains(event.relatedTarget) && setHover(null),
      }, state.items.map(({ li }) => li));
    }

    function set(ours, theirs) {
      [keep.ours, keep.theirs] = [ours, theirs];
      show();
    }

    const STAGES = {
      read: () => [[terminal("conflict-merge"), editor(words.file.conflicted, false, markedFile())], null],
      choose: (choice) => [[editor(words.file.conflicted, false, markedFile())], [keepBox(choice, set, words), editor(choice ? words.file.saved : words.file.nothing, Boolean(choice), cleanFile(conflict, sides, choice, words))]],
      add: (choice) => [[terminal("conflict-status", `conflict-add-${choice}`)], [editor(words.file.added, true, cleanFile(conflict, sides, choice, words))]],
      commit: (choice) => [[diamond(conflict, choice, words), terminal(`conflict-commit-${choice}`)], [editor(words.file.committed, true, cleanFile(conflict, sides, choice, words))]],
    };

    function render(step) {
      state.step = step;
      state.hover = null;
      const stage = STEPS[state.step].stage;
      const [leftParts, rightParts] = STAGES[stage](outcome());
      left.replaceChildren(...leftParts);
      if (rightParts) right.replaceChildren(...rightParts);
      if (stage === "read" || stage === "choose") paint();
    }

    const steps = story(words, (index) => STEPS[index].stage !== "choose" || outcome() !== null, render);
    const show = steps.refresh;

    const element = el("section", { class: "art-ig guide-conflict", id: "guide-conflict", tabindex: "-1", "aria-labelledby": "guide-conflict-title" },
      el("h2", { class: "art-ig-title", id: "guide-conflict-title" }, words.title),
      el("p", { class: "gx-lede" }, words.lede),
      steps.element,
      el("div", { class: "gx-layout", onpointerdown: (event) => !event.target.closest(".gx-file") && setHover(null) }, left, right));
    show();
    return { element };
  }

  return { create };
})();
