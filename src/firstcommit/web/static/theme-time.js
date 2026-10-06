"use strict";

/*
 * The time-travel look, drawn through map.js's theme hook; the colours and type are in
 * theme-time.css. A commit is a save point (a snapshot of every tracked file), a branch is a
 * timeline, HEAD is "now" (the commit you are on), a merge commit is where timelines join, a tag
 * is a milestone, and a remote-tracking branch is where a branch was last seen in the shared
 * archive (the remote). The metaphor never replaces Git's words: every save point keeps its real
 * short hash and subject, every chip its real name, HEAD's chip reads HEAD, and the key under the
 * graph puts each metaphor next to its Git word. Needs dom.js and map.js. Defines one global,
 * TimeTheme: `map` (a RepoMap theme), `panel` (LivePanel's titles), `legend(layout)` and
 * `tabKey(label)`, the name theme-time-motion.js follows a tab by.
 */

/* global Dom, RepoMap */
/* exported TimeTheme */

const TimeTheme = (function () {
  const { el, svg } = Dom;
  const DIAL_TICKS = 12;
  const POINT = 7;
  const NOTCH = 5;

  /* Each entry: the metaphor, Git's word, and what the Git word means when that is worth saying. */
  const LEGEND = {
    commit: ["save point", "commit", "a snapshot of every tracked file"],
    branch: ["timeline", "branch", null],
    merge: ["timelines joining", "merge commit", null],
    tag: ["milestone", "tag", null],
    remote: ["last seen in the shared archive", "remote-tracking branch", null],
  };

  /* The legend entries a layout needs, in the legend's order: only what the map shows. */
  function legend(map) {
    const kinds = new Set(map.commits.flatMap((commit) => commit.labels.map((label) => label.kind)));
    const shown = {
      commit: map.commits.length > 0,
      branch: kinds.has("branch"),
      merge: map.commits.some((commit) => commit.isMerge),
      tag: kinds.has("tag"),
      remote: kinds.has("remote"),
    };
    return Object.keys(LEGEND).filter((entry) => shown[entry]);
  }

  /* A save point is a ring around a solid core; a merge commit adds an outer ring, and HEAD's
     commit sits inside the now mark, a dial of twelve ticks. */
  function savePoint({ x, y, color, theme, isHead, isMerge }) {
    const { radius } = theme.sizes;
    const dial = radius + 8;
    const tick = (2 * Math.PI * dial) / DIAL_TICKS;
    return svg("g", { class: "tt-point", style: `--color: ${color}` },
      isHead && svg("g", { class: "tt-now", style: `--color: ${theme.colors.head}` },
        svg("circle", { class: "tt-now-glow", cx: x, cy: y, r: dial + 3 }),
        svg("circle", { class: "tt-now-dial", cx: x, cy: y, r: dial, "stroke-dasharray": `${tick * 0.28} ${tick * 0.72}`, "stroke-dashoffset": tick * 0.14 }),
      ),
      isMerge && svg("circle", { class: "tt-join", cx: x, cy: y, r: radius + 3.5 }),
      svg("circle", { class: "tt-save", cx: x, cy: y, r: radius }),
      svg("circle", { class: "tt-core", cx: x, cy: y, r: radius - 3.25 }),
    );
  }

  const timeline = ({ edge, color }) => svg("path", {
    class: `map-edge tt-edge is-${edge.kind}${edge.lane === 0 ? " is-first" : ""}`, d: edge.d, style: `--color: ${color}`, "data-from": edge.from, "data-to": edge.to,
  });

  /* The name a tab keeps from one drawing to the next: HEAD's tab is one, detached or not. */
  const tabKey = (label) => (label.kind === "head" ? "head" : `${label.kind}:${label.text}`);

  /* HEAD's chip points left at its commit and a tag is a pennant; other chips are plain tabs. */
  const OUTLINES = {
    head: (x, top, width, height) => {
      const right = x + width;
      const bottom = top + height;
      return `M${x},${top + height / 2} L${x + POINT},${top} H${right - 4} Q${right},${top} ${right},${top + 4} V${bottom - 4} Q${right},${bottom} ${right - 4},${bottom} H${x + POINT} Z`;
    },
    tag: (x, top, width, height) => `M${x},${top} H${x + width} L${x + width - NOTCH},${top + height / 2} L${x + width},${top + height} H${x} Z`,
  };
  const TEXT_SHIFT = { head: POINT / 3, tag: -NOTCH / 3 };

  function chipShape(kind, x, top, width, height) {
    if (OUTLINES[kind]) return svg("path", { class: "tt-chip", d: OUTLINES[kind](x, top, width, height) });
    return svg("rect", { class: "tt-chip", x, y: top, width, height, rx: 4 });
  }

  function chip({ label, x, y, color, theme }) {
    const { chipHeight } = theme.sizes;
    return svg("g", { class: `map-label is-${label.kind}${label.current ? " is-current" : ""}`, style: `--color: ${color}`, "data-label": tabKey(label) },
      chipShape(label.kind, x, y - chipHeight / 2, label.width, chipHeight),
      svg("text", { x: x + label.width / 2 + (TEXT_SHIFT[label.kind] || 0), y, "text-anchor": "middle", "dominant-baseline": "central" }, label.text),
    );
  }

  /* A small picture for the key, drawn with the graph's own shapes: [viewBox, nodes]. */
  function mark(entry, theme) {
    const { lanes, tag, remote } = theme.colors;
    const point = (isHead, isMerge) => savePoint({ x: 20, y: 20, color: lanes[0], theme, isHead, isMerge });
    const pictures = {
      now: () => ["0 0 40 40", point(true, false)],
      commit: () => ["8 8 24 24", point(false, false)],
      merge: () => ["8 8 24 24", point(false, true)],
      branch: () => ["0 0 24 24", [
        svg("path", { class: "map-edge tt-edge is-first", d: "M7,24 V0", style: `--color: ${lanes[0]}` }),
        svg("path", { class: "map-edge tt-edge is-fork", d: "M7,19 C7,12 18,13 18,6 V0", style: `--color: ${lanes[1]}` }),
      ]],
      tag: () => ["0 0 24 24", svg("g", { class: "map-label is-tag", style: `--color: ${tag}` }, chipShape("tag", 1, 6, 22, 12))],
      remote: () => ["0 0 24 24", svg("g", { class: "map-label is-remote", style: `--color: ${remote}` }, chipShape("remote", 1, 6, 22, 12))],
    };
    const [viewBox, picture] = pictures[entry]();
    return svg("svg", { class: `tt-mark is-${entry}`, width: 22, height: 22, viewBox, "aria-hidden": "true", focusable: "false" }, picture);
  }

  function key({ snapshot, map, theme }) {
    const { words } = theme;
    return el("div", { class: "map-key tt-key" },
      el("p", { class: "tt-key-now" }, mark("now", theme), el("span", {}, el("b", {}, words.now), ": ", snapshot.branch ? words.here : words.hereDetached)),
      el("ul", { class: "tt-legend", "aria-label": words.legend },
        legend(map).map((entry) => {
          const [metaphor, git, meaning] = LEGEND[entry];
          return el("li", {}, mark(entry, theme), el("span", {}, metaphor, " = ", el("b", {}, git), meaning && `: ${meaning}`));
        }),
      ),
    );
  }

  const map = RepoMap.theme({
    sizes: { pad: 16, row: 34, lane: 24, radius: 6, gap: 14, chipPad: 8, chipHeight: 21, char: 7.8, subject: 48 },
    words: {
      now: "HEAD = now",
      here: "the commit you are on. Your next commit goes on top of it.",
      hereDetached: "the commit you are on, with no branch (detached HEAD). Your next commit goes on top of it.",
      legend: "What the drawing means",
      unborn: (branch) => `You are on ${branch}, which has no commits yet. Your first commit starts its timeline.`,
      summary: ({ count, head, branch }) => `Commit graph drawn as timelines, ${count} ${count === 1 ? "commit" : "commits"}.${head ? ` HEAD, now, is at ${head}${branch ? ` on ${branch}` : ", detached"}.` : ""}`,
    },
    shapes: { commit: savePoint, edge: timeline, label: chip, key },
  });

  const panel = {
    project: "Your repository · its timelines",
    github: "GitHub (the practice copy) · shared archive",
    areas: "The three areas",
    feed: "What just happened",
  };

  return { map, panel, legend, tabKey };
})();
