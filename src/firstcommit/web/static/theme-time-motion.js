"use strict";

/*
 * The time-travel map's motions: what changed between two drawings of the same repository, and
 * how to show it. Nothing is invented: every motion is a difference between the two snapshots,
 * the same pair the "what just happened" feed describes.
 *
 * motions(before, after, sizes) compares two layouts (RepoMap.layout) and is pure. Positions
 * are on the new drawing:
 * - born: commits drawn now and not before; they grow in.
 * - appear: tabs (TimeTheme.tabKey) that are new, or whose old commit has no place on the new
 *   drawing; they fade in.
 * - slides: tabs that moved, as {key, dx, dy}: where they were minus where they are. A tab
 *   that moved to another commit slides from that commit; one that stayed shifts sideways when
 *   the tabs before it changed.
 * - texts: commits drawn both times whose hash and subject start elsewhere because the tabs
 *   before them changed, as {hash, dx}; they slide sideways with the tabs.
 * - dial: HEAD's dial, {dx, dy}, when HEAD is on another commit. When HEAD's tab appears
 *   instead (HEAD had no commit before, as after a clone), the dial fades in with it.
 * - ghosts: commits no longer drawn (a reset, an amend, a rebase, a deleted branch), placed
 *   where they were relative to their nearest first-parent ancestor still drawn, with their
 *   short hash and subject; they fade out. `replacedBy` names the new commit drawn in the very
 *   same place (an amend, a rebase): that ghost fades first and its replacement appears after.
 * - lines: the lines from each new commit to its parents; they draw in from the parent, so a new
 *   commit grows from the one it was made on, and a merge visibly joins two timelines.
 * - lift: how far to hold the drawing down at first so a ghost or a starting tab above the top
 *   row shows, before the drawing settles.
 * play(figure, motion, theme, reduced, offset) runs them on the figure RepoMap.render just drew,
 * all over within 750 ms of `offset`, with the Web Animations API; under prefers-reduced-motion
 * it does nothing.
 * Needs dom.js and theme-time.js. Defines one global, TimeMotion.
 */

/* global Dom, TimeTheme */
/* exported TimeMotion */

const TimeMotion = (function () {
  const { svg } = Dom;
  const EASE = "cubic-bezier(0.2, 0.8, 0.2, 1)";
  const SAVE_POINT = /^tt-(join|save|core)$/;
  const TIMING = {
    born: { duration: 330 },
    replaced: { duration: 250 },
    replacing: { delay: 250, duration: 330 },
    appear: { delay: 150, duration: 330 },
    slide: { delay: 130, duration: 480 },
    line: { delay: 50, duration: 450 },
    ghost: { delay: 380, duration: 330 },
    lift: { delay: 480, duration: 250 },
  };

  const empty = () => ({ born: [], appear: [], slides: [], texts: [], dial: null, ghosts: [], lines: [], lift: 0 });

  /* Where a commit's hash and subject start: after its tabs. */
  const textX = (map, commit, sizes) => commit.labels.reduce((x, label) => x + label.width + sizes.chipPad, map.textStart);

  function textMoves(before, after, sizes) {
    const old = new Map(before.commits.map((commit) => [commit.hash, commit]));
    return after.commits
      .filter((commit) => old.has(commit.hash))
      .map((commit) => ({ hash: commit.hash, dx: textX(before, old.get(commit.hash), sizes) - textX(after, commit, sizes) }))
      .filter((move) => move.dx !== 0);
  }

  /* Each tab of a layout: key -> {hash, offset}, its commit and its distance from the first tab. */
  function tabs(map, sizes) {
    const found = new Map();
    for (const commit of map.commits) {
      let offset = 0;
      for (const label of commit.labels) {
        found.set(TimeTheme.tabKey(label), { hash: commit.hash, offset });
        offset += label.width + sizes.chipPad;
      }
    }
    return found;
  }

  /* Where a commit of either drawing goes on the new one: its own place while it is still drawn,
     else its old place relative to its nearest first-parent ancestor still drawn, else null. */
  function placer(before, after) {
    const old = new Map(before.commits.map((commit) => [commit.hash, commit]));
    const now = new Map(after.commits.map((commit) => [commit.hash, commit]));
    return (hash) => {
      if (now.has(hash)) return { x: now.get(hash).x, y: now.get(hash).y };
      let anchor = old.get(hash);
      while (anchor && !now.has(anchor.hash)) anchor = old.get(anchor.parents[0]);
      if (!anchor) return null;
      const [was, kept] = [old.get(hash), now.get(anchor.hash)];
      return { x: kept.x + was.x - anchor.x, y: kept.y + was.y - anchor.y };
    };
  }

  function tabMoves(before, after, sizes, place) {
    const old = tabs(before, sizes);
    const byHash = new Map(after.commits.map((commit) => [commit.hash, commit]));
    const appear = [];
    const slides = [];
    for (const [key, tab] of tabs(after, sizes)) {
      const was = old.get(key);
      const from = was ? place(was.hash) : null;
      const dx = from ? before.textStart + was.offset - (after.textStart + tab.offset) : 0;
      const dy = from ? from.y - byHash.get(tab.hash).y : 0;
      if (!from) appear.push(key);
      else if (dx !== 0 || dy !== 0) slides.push({ key, dx, dy });
    }
    return { appear, slides };
  }

  function dialMove(before, after, place) {
    const was = before.commits.find((commit) => commit.isHead);
    const now = after.commits.find((commit) => commit.isHead);
    const from = was && now && was.hash !== now.hash ? place(was.hash) : null;
    return from && (from.x !== now.x || from.y !== now.y) ? { dx: from.x - now.x, dy: from.y - now.y } : null;
  }

  function motions(before, after, sizes) {
    if (!before || !after) return empty();
    const place = placer(before, after);
    const drawnBefore = new Set(before.commits.map((commit) => commit.hash));
    const drawnAfter = new Set(after.commits.map((commit) => commit.hash));
    const born = after.commits.filter((commit) => !drawnBefore.has(commit.hash));
    const { appear, slides } = tabMoves(before, after, sizes, place);
    const dial = dialMove(before, after, place);
    const ghosts = before.commits.filter((commit) => !drawnAfter.has(commit.hash) && place(commit.hash)).map((commit) => ({
      hash: commit.hash,
      short: commit.short,
      subject: commit.subject,
      ...place(commit.hash),
      textX: after.textStart + textX(before, commit, sizes) - before.textStart,
      lane: commit.lane,
      parent: commit.parents.length ? place(commit.parents[0]) : null,
    })).map((ghost) => ({ ...ghost, replacedBy: (born.find((commit) => commit.x === ghost.x && commit.y === ghost.y) || { hash: null }).hash }));
    const lines = born.flatMap((commit) => commit.parents.map((to) => ({ from: commit.hash, to })));
    const yOf = new Map(after.commits.map((commit) => [commit.hash, commit.y]));
    const tabsAt = tabs(after, sizes);
    const starts = [
      ...ghosts.map((ghost) => ghost.y),
      ...slides.map((slide) => yOf.get(tabsAt.get(slide.key).hash) + slide.dy),
      ...(dial ? [after.commits.find((commit) => commit.isHead).y + dial.dy] : []),
    ];
    const top = sizes.pad + sizes.row / 2;
    const lift = Math.max(0, top - Math.min(top, ...starts));
    return { born: born.map((commit) => commit.hash), appear, slides, texts: textMoves(before, after, sizes), dial, ghosts, lines, lift };
  }

  const shift = (dx, dy) => `translate(${dx}px, ${dy}px)`;

  function ghostLayer(ghosts, theme) {
    const { colors, sizes } = theme;
    return svg("g", { class: "tt-ghosts", "aria-hidden": "true" }, ghosts.map((ghost) => svg("g", { class: "tt-ghost", style: `--color: ${colors.lanes[ghost.lane % colors.lanes.length]}` },
      ghost.parent && svg("path", { class: "tt-ghost-line", d: `M${ghost.x},${ghost.y} L${ghost.parent.x},${ghost.parent.y}` }),
      svg("circle", { class: "tt-save", cx: ghost.x, cy: ghost.y, r: sizes.radius }),
      svg("text", { class: "map-hash", x: ghost.textX, y: ghost.y, "dominant-baseline": "central" }, ghost.short),
      svg("text", { class: "map-subject", x: ghost.textX + (ghost.short.length + 1) * sizes.char, y: ghost.y, "dominant-baseline": "central" }, ` ${ghost.subject}`.slice(1)),
    )));
  }

  /* A new commit's own circles (not HEAD's dial) grow in, and its hash and subject fade in. */
  function bear(graph, hash, timing, animate) {
    const commit = graph.querySelector(`[data-hash="${hash}"]`);
    const circles = [...commit.querySelector(".tt-point").children].filter((node) => SAVE_POINT.test(node.getAttribute("class")));
    for (const circle of circles) animate(circle, [{ opacity: 0, transform: "scale(0.4)" }, { opacity: 1, transform: "scale(1)" }], timing);
    for (const text of [commit.querySelector(".map-hash"), commit.querySelector(".map-subject")]) animate(text, [{ opacity: 0 }, { opacity: 1 }], timing);
  }

  /* A new commit's line to a parent draws in, from the parent up to the new commit. */
  function draw(graph, { from, to }, animate) {
    const line = [...graph.querySelectorAll(".tt-edge")].find((path) => path.getAttribute("data-from") === from && path.getAttribute("data-to") === to);
    const length = line.getTotalLength();
    line.style.strokeDasharray = `${length} ${length}`;
    animate(line, [{ strokeDashoffset: -length }, { strokeDashoffset: 0 }], TIMING.line).onfinish = () => line.style.removeProperty("stroke-dasharray");
  }

  /* The ghosts go under the commits, fade (replaced ones first), and are removed once faded. */
  function haunt(graph, ghosts, theme, animate) {
    for (const replaced of [true, false]) {
      const some = ghosts.filter((ghost) => Boolean(ghost.replacedBy) === replaced);
      if (!some.length) continue;
      const layer = ghostLayer(some, theme);
      graph.insertBefore(layer, graph.querySelector(".map-commits"));
      animate(layer, [{ opacity: 1 }, { opacity: 0 }], { ...(replaced ? TIMING.replaced : TIMING.ghost), fill: "both" }).onfinish = () => layer.remove();
    }
  }

  /* Runs `motion` on a figure RepoMap.render just drew, every part `offset` ms later; returns the
     animations it started. */
  function play(figure, motion, theme, reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches, offset = 0) {
    const graph = figure.querySelector(".map-graph");
    if (reduced || !graph || typeof graph.animate !== "function") return [];
    const started = [];
    const animate = (node, frames, timing) => {
      const animation = node.animate(frames, { easing: EASE, fill: "backwards", ...timing, delay: (timing.delay || 0) + offset });
      started.push(animation);
      return animation;
    };
    const slide = (node, { dx, dy }, timing) => node && animate(node, [{ transform: shift(dx, dy) }, { transform: shift(0, 0) }], timing);
    const tab = (key) => [...graph.querySelectorAll("[data-label]")].find((node) => node.getAttribute("data-label") === key);
    const replacing = new Set(motion.ghosts.map((ghost) => ghost.replacedBy));
    motion.born.forEach((hash) => bear(graph, hash, replacing.has(hash) ? TIMING.replacing : TIMING.born, animate));
    motion.appear.map(tab).filter(Boolean).forEach((node) => animate(node, [{ opacity: 0 }, { opacity: 1 }], TIMING.appear));
    motion.slides.forEach((move) => slide(tab(move.key), move, TIMING.slide));
    for (const { hash, dx } of motion.texts) {
      const commit = graph.querySelector(`[data-hash="${hash}"]`);
      for (const text of [commit.querySelector(".map-hash"), commit.querySelector(".map-subject")]) slide(text, { dx, dy: 0 }, TIMING.slide);
    }
    const dial = graph.querySelector(".map-commit.is-head .tt-now");
    if (motion.dial) slide(dial, motion.dial, TIMING.slide);
    else if (dial && motion.appear.includes("head")) animate(dial, [{ opacity: 0 }, { opacity: 1 }], TIMING.appear);
    motion.lines.forEach((line) => draw(graph, line, animate));
    if (motion.ghosts.length) haunt(graph, motion.ghosts, theme, animate);
    if (motion.lift) animate(graph, [{ marginTop: `${motion.lift}px` }, { marginTop: "0px" }], TIMING.lift);
    return started;
  }

  return { motions, play, TIMING };
})();
