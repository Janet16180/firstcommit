"use strict";

/*
 * The time-travel look, drawn through map.js's theme hook; the colours and type are in
 * theme-time.css. A commit is a save point (a snapshot of every tracked file), a branch is a
 * timeline, HEAD is "now" (the commit you are on), a merge commit is where timelines join, a tag
 * is a milestone, and a remote-tracking branch is where a branch was last seen in the shared
 * archive (the remote). The metaphor never replaces Git's words: every save point keeps its real
 * short hash and subject, every chip its real name, HEAD's chip reads HEAD, and the key under the
 * graph puts each metaphor next to its Git word. Needs dom.js and map.js. Defines one global,
 * TimeTheme: `map` (a RepoMap theme), `small` (the same map, smaller and with no key, for
 * figures), `boxes` (`small` with each commit drawn as a closed box), `live` (`map` with each
 * commit drawn as the live page's four places draw it), `withGuide(guide, base)` (`base`, or
 * `map`, with the button of TimeGuide's `guide` in its key), `panel` (LivePanel's
 * titles), `terminal` (xterm colours, light and dark), `legend(layout)`, `mark(name)` (the small
 * picture the key and the guide put beside a word) and `tabKey(label)`, the name
 * theme-time-motion.js follows a tab by.
 */

/* global Dom, RepoMap */
/* exported TimeTheme */

const TimeTheme = (function () {
  const { el, svg } = Dom;
  const DIAL_TICKS = 12;
  const POINT = 7;
  const NOTCH = 5;

  /* Each entry: the metaphor, Git's word, and what the Git word means when that is worth saying.
     A commit's metaphor is the theme's (`words.commit`), as its picture is the theme's shape. */
  const LEGEND = {
    commit: [null, "commit", "a snapshot of every tracked file"],
    branch: ["timeline", "branch", null],
    merge: ["timelines joining", "merge commit", null],
    tag: ["milestone", "tag", null],
    remote: ["last seen in the archive", "remote-tracking branch", null],
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

  /* The now mark around HEAD's commit: a dial of twelve ticks. */
  function nowDial(x, y, theme) {
    const dial = theme.sizes.radius + 8;
    const tick = (2 * Math.PI * dial) / DIAL_TICKS;
    return svg("g", { class: "tt-now", style: `--color: ${theme.colors.head}` },
      svg("circle", { class: "tt-now-glow", cx: x, cy: y, r: dial + 3 }),
      svg("circle", { class: "tt-now-dial", cx: x, cy: y, r: dial, "stroke-dasharray": `${tick * 0.28} ${tick * 0.72}`, "stroke-dashoffset": tick * 0.14 }),
    );
  }

  /* A save point is a ring around a solid core; a merge commit adds an outer ring, and HEAD's
     commit sits inside the now mark. */
  function savePoint({ x, y, color, theme, isHead, isMerge }) {
    const { radius } = theme.sizes;
    return svg("g", { class: "tt-point", style: `--color: ${color}` },
      isHead && nowDial(x, y, theme),
      isMerge && svg("circle", { class: "tt-join", cx: x, cy: y, r: radius + 3.5 }),
      svg("circle", { class: "tt-save", cx: x, cy: y, r: radius }),
      svg("circle", { class: "tt-core", cx: x, cy: y, r: radius - 3.25 }),
    );
  }

  /* The same commit as a closed box, for the first chapters' pictures: a box under its lid, an
     outer frame for a merge commit, and the now mark around HEAD's. Its parts keep a save point's
     class names, so the motions grow it in the same way. */
  function closedBox({ x, y, color, theme, isHead, isMerge }) {
    const half = theme.sizes.radius + 2;
    return svg("g", { class: "tt-point tt-box", style: `--color: ${color}` },
      isHead && nowDial(x, y, theme),
      isMerge && svg("rect", { class: "tt-join", x: x - half - 3, y: y - half - 3, width: 2 * half + 6, height: 2 * half + 6, rx: 3 }),
      svg("rect", { class: "tt-save", x: x - half, y: y - half + 2, width: 2 * half, height: 2 * half - 2, rx: 1.5 }),
      svg("rect", { class: "tt-core", x: x - half - 1, y: y - half, width: 2 * half + 2, height: 3.5, rx: 1 }),
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

  /* A small picture for the key, drawn with the graph's own shapes: [viewBox, nodes]. A commit
     is drawn with the theme's commit shape, so a map of boxes has boxes in its key. */
  function mark(entry, theme) {
    const { lanes, tag, remote } = theme.colors;
    const middle = theme.sizes.radius + 14;
    const point = (isHead, isMerge) => theme.shapes.commit({ x: middle, y: middle, color: lanes[0], theme, isHead, isMerge });
    const around = (reach) => `${middle - reach} ${middle - reach} ${2 * reach} ${2 * reach}`;
    const pictures = {
      now: () => [around(middle), point(true, false)],
      commit: () => [around(theme.sizes.radius + 6), point(false, false)],
      merge: () => [around(theme.sizes.radius + 6), point(false, true)],
      branch: () => ["0 0 24 24", [
        svg("path", { class: "map-edge tt-edge is-first", d: "M7,24 V0", style: `--color: ${lanes[0]}` }),
        svg("path", { class: "map-edge tt-edge is-fork", d: "M7,19 C7,12 18,13 18,6 V0", style: `--color: ${lanes[1]}` }),
      ]],
      line: () => ["0 0 24 24", [
        svg("path", { class: "map-edge tt-edge is-first", d: "M12,5 V19", style: `--color: ${lanes[0]}` }),
        [5, 19].map((y) => svg("g", { class: "tt-point", style: `--color: ${lanes[0]}` }, svg("circle", { class: "tt-save", cx: 12, cy: y, r: 3.5 }))),
      ]],
      archive: () => ["0 0 24 24", svg("g", { class: "tt-archive", style: `--color: ${remote}` },
        svg("rect", { x: 3, y: 4, width: 18, height: 5, rx: 1 }),
        svg("path", { d: "M5,9 V20 H19 V9 M10,13 H14" }),
      )],
      tag: () => ["0 0 24 24", svg("g", { class: "map-label is-tag", style: `--color: ${tag}` }, chipShape("tag", 1, 6, 22, 12))],
      remote: () => ["0 0 24 24", svg("g", { class: "map-label is-remote", style: `--color: ${remote}` }, chipShape("remote", 1, 6, 22, 12))],
    };
    const [viewBox, picture] = pictures[entry]();
    return svg("svg", { class: `tt-mark is-${entry}`, width: 22, height: 22, viewBox, "aria-hidden": "true", focusable: "false" }, picture);
  }

  /* The key under the map; `guide` (TimeGuide's) adds its button at the end of HEAD's line. */
  function key({ snapshot, map, theme }, guide = null) {
    const { words } = theme;
    return el("div", { class: "map-key tt-key" },
      el("p", { class: "tt-key-now" }, mark("now", theme), el("span", {}, el("b", {}, words.now), ": ", snapshot.branch ? words.here : words.hereDetached), guide && guide.button()),
      el("ul", { class: "tt-legend", "aria-label": words.legend },
        legend(map).map((entry) => {
          const [metaphor, git, meaning] = LEGEND[entry];
          return el("li", {}, mark(entry, theme), el("span", {}, metaphor || words[entry], " = ", el("b", {}, git), meaning && `: ${meaning}`));
        }),
      ),
    );
  }

  const map = RepoMap.theme({
    sizes: { pad: 16, row: 34, lane: 24, radius: 6, gap: 14, chipPad: 8, chipHeight: 21, char: 7.8, subject: 48 },
    words: {
      commit: "save point",
      now: "HEAD = now",
      here: "the commit you are on.",
      hereDetached: "the commit you are on, with no branch (detached HEAD).",
      legend: "What the drawing means",
      unborn: (branch) => `You are on ${branch}, which has no commits yet. Your first commit starts its timeline.`,
      summary: ({ count, head, branch }) => `Commit graph drawn as timelines, ${count} ${count === 1 ? "commit" : "commits"}.${head ? ` HEAD, now, is at ${head}${branch ? ` on ${branch}` : ", detached"}.` : ""}`,
    },
    shapes: { commit: savePoint, edge: timeline, label: chip, key },
  });

  /* The same map, smaller and with no key, for figures: the four places and the guide's pictures. */
  const small = RepoMap.theme({
    trunk: map.trunk,
    sizes: { pad: 10, row: 28, lane: 18, radius: 5, gap: 10, chipPad: 6, chipHeight: 18, char: 6.6, subject: 24 },
    colors: map.colors,
    words: map.words,
    shapes: { ...map.shapes, key: () => null },
  });

  /* The small map with each commit drawn as a closed box. */
  const boxes = RepoMap.theme({ ...small, words: { ...small.words, commit: "closed box" }, shapes: { ...small.shapes, commit: closedBox } });

  /* How the live page draws a commit, in the four places: the one switch between a closed box and
     a save point (`{ shape: savePoint, word: "save point" }` draws rings). */
  const LIVE_COMMIT = { shape: closedBox, word: "closed box" };

  /* The live page's map: the map's own size, each commit drawn as LIVE_COMMIT says. */
  const live = RepoMap.theme({ ...map, words: { ...map.words, commit: LIVE_COMMIT.word }, shapes: { ...map.shapes, commit: LIVE_COMMIT.shape } });

  const panel = {
    project: "Your repository · its timelines",
    github: "GitHub (the practice copy) · shared archive",
    areas: "The three areas",
    places: "The four places",
    feed: "What just happened",
  };

  /* xterm colours on the theme's warm paper and ink; every colour Git uses for text stays readable. */
  const terminal = {
    light: {
      background: "#fdf9f1", foreground: "#2b2620", cursor: "#1b6e68", cursorAccent: "#fdf9f1", selectionBackground: "#e9dfcf",
      black: "#2b2620", red: "#a8321f", green: "#2f6f2c", yellow: "#7d5700", blue: "#285e96", magenta: "#7d4a8c", cyan: "#12706b", white: "#675c4f",
      brightBlack: "#8a7d6c", brightRed: "#b8402c", brightGreen: "#3a7d36", brightYellow: "#8a6100", brightBlue: "#2f62a3", brightMagenta: "#8b55a0", brightCyan: "#167a74", brightWhite: "#5e5448",
    },
    dark: {
      background: "#1a1713", foreground: "#ece5d8", cursor: "#5ec8bd", cursorAccent: "#1a1713", selectionBackground: "#3a3328",
      black: "#4a4339", red: "#f0928a", green: "#9ad08e", yellow: "#e8c06a", blue: "#93bff0", magenta: "#d6a2e6", cyan: "#6fd0c8", white: "#d9d0c1",
      brightBlack: "#8a7f70", brightRed: "#ffaaa1", brightGreen: "#b3e3a8", brightYellow: "#f5d58a", brightBlue: "#b0d0f5", brightMagenta: "#e5bdf2", brightCyan: "#93e0d8", brightWhite: "#f7f1e6",
    },
  };

  /* A map (`map` unless given) with the guide's button in its key. */
  const withGuide = (guide, base = map) => RepoMap.theme({ ...base, shapes: { ...base.shapes, key: (ctx) => key(ctx, guide) } });

  return { map, small, boxes, live, withGuide, panel, legend, tabKey, terminal, mark: (name) => mark(name, map) };
})();
