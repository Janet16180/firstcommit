"use strict";

/*
 * The live map: a repository snapshot (firstcommit/repomap.py's Snapshot) drawn as a commit
 * graph, the three areas strip, and the object list. Needs dom.js. Defines one global, RepoMap.
 *
 * The layout is pure and separate from the drawing: `layout(snapshot, options)` places every
 * commit on a row (newest at the top, children always above their parents) and a lane, and
 * lists the edges and labels; `render(snapshot, options)` draws it as SVG.
 *
 * Lanes: each branch tip, then HEAD, then remote-tracking branches, then tags, claims the
 * commits of its first-parent line that no earlier tip claimed. The trunk branch names
 * (`theme.trunk`, main and master by default) claim first, so main keeps lane 0 whichever
 * branch HEAD is on. A line keeps a lane from its newest commit to the commit it started
 * from; lanes are reused once free, so merged branches do not widen the map forever.
 *
 * Theme hook: `RepoMap.theme(overrides)` gives a theme to pass as `options.theme`. Every part
 * is optional and merges over DEFAULT_THEME:
 * - trunk: branch names given the first lanes, in order.
 * - sizes: pad, row (row height), lane (lane width), radius (commit dot), gap (graph to labels),
 *   chipPad and chipHeight (labels), char (width of one character of label text), subject
 *   (longest subject shown, in characters), all in pixels except `subject`.
 * - colors: lanes (a list, by lane), head, branch, remote and tag. Any CSS colour or var(...):
 *   they are handed to the shapes, which set them as the `--color` custom property.
 * - words: every text the map shows (some are functions of a count or a name).
 * - shapes: commit(ctx), edge(ctx) and label(ctx) return the SVG node(s) for one commit dot,
 *   one edge path or one label chip. `ctx` has the position, `color`, the theme, and the
 *   commit, edge or label; RepoMap.svg makes SVG elements. The map adds the classes
 *   map-commit (is-head, is-new, is-merge), the commit's tooltip, and the hash and subject.
 *   key(ctx) returns the element under the graph that explains HEAD's mark (and anything else
 *   the theme wants to explain); `ctx` has the snapshot, the map (the layout) and the theme.
 * The default look comes from map rules in app.css and the --map-* custom properties, which a
 * theme stylesheet can also change.
 */

/* global Dom */
/* exported RepoMap */

const RepoMap = (function () {
  const { el, svg } = Dom;
  const FOLD_UNCHANGED = 8;

  const shapes = {
    commit: ({ x, y, color, theme, isHead }) => [
      isHead && svg("circle", { class: "map-halo", cx: x, cy: y, r: theme.sizes.radius + 5, style: `--color: ${theme.colors.head}` }),
      svg("circle", { class: "map-dot", cx: x, cy: y, r: theme.sizes.radius, style: `--color: ${color}` }),
    ],
    edge: ({ edge, color }) => svg("path", { class: `map-edge is-${edge.kind}`, d: edge.d, style: `--color: ${color}` }),
    label: ({ label, x, y, color, theme }) => {
      const { chipHeight } = theme.sizes;
      return svg("g", { class: `map-label is-${label.kind}${label.current ? " is-current" : ""}`, style: `--color: ${color}` },
        svg("rect", { x, y: y - chipHeight / 2, width: label.width, height: chipHeight, rx: chipHeight / 2 }),
        svg("text", { x: x + label.width / 2, y, "text-anchor": "middle", "dominant-baseline": "central" }, label.text),
      );
    },
    key,
  };

  const DEFAULT_THEME = {
    trunk: ["main", "master"],
    sizes: { pad: 14, row: 34, lane: 22, radius: 6, gap: 12, chipPad: 8, chipHeight: 20, char: 7.8, subject: 48 },
    colors: {
      lanes: [0, 1, 2, 3, 4, 5].map((lane) => `var(--map-lane-${lane})`),
      head: "var(--map-head)",
      branch: "var(--map-branch)",
      remote: "var(--map-remote)",
      tag: "var(--map-tag)",
    },
    words: {
      head: "HEAD",
      detachedHead: "HEAD (detached)",
      here: "HEAD: you are here",
      hereDetached: "HEAD: you are here, on no branch (detached)",
      noRepository: "No repository in this folder yet.",
      noCommits: "No commits yet.",
      unborn: (branch) => `You are on ${branch}, which has no commits yet.`,
      operation: (name) => `A ${name} is in progress.`,
      stash: (count) => `${count} stashed ${count === 1 ? "change" : "changes"} (git stash list).`,
      truncated: (count) => `Showing the newest ${count} commits.`,
      summary: ({ count, head, branch }) => `Commit graph, ${count} ${count === 1 ? "commit" : "commits"}.${head ? ` HEAD is at ${head}${branch ? ` on ${branch}` : ", detached"}.` : ""}`,
      areas: {
        file: "File",
        folder: "Working folder",
        index: "Staging area",
        head: "Last commit",
        add: "git add",
        commit: "git commit",
        empty: "No files in the working folder yet.",
        unchanged: (count) => `${count} unchanged files`,
        show: "Show them",
        repository: "a separate repository",
      },
      /* git status's two columns: how the working folder differs from the staging area, and how
         the staging area differs from the last commit. */
      states: {
        folder: { modified: "modified, not staged", deleted: "deleted, not staged", typechange: "type changed, not staged", untracked: "untracked", ignored: "ignored" },
        index: { added: "new file, staged", modified: "modified, staged", deleted: "deleted, staged", typechange: "type changed, staged", conflicted: "in conflict" },
      },
      objects: { type: "Type", hash: "Hash", size: "Size", bytes: (count) => `${count} B`, empty: "No objects yet." },
    },
    shapes,
  };

  /* A theme: the default with the given parts merged over it, one level deep. */
  function themeWith(overrides) {
    const merged = { ...DEFAULT_THEME, trunk: overrides.trunk || DEFAULT_THEME.trunk };
    for (const part of ["sizes", "colors", "words", "shapes"]) merged[part] = { ...DEFAULT_THEME[part], ...(overrides[part] || {}) };
    return merged;
  }

  /* The commits with every child before its parents, otherwise in the order given. */
  function order(commits) {
    const known = new Set(commits.map((commit) => commit.hash));
    const children = new Map(commits.map((commit) => [commit.hash, 0]));
    for (const commit of commits) {
      for (const parent of commit.parents) if (known.has(parent)) children.set(parent, children.get(parent) + 1);
    }
    const ready = commits.filter((commit) => children.get(commit.hash) === 0);
    const byHash = new Map(commits.map((commit) => [commit.hash, commit]));
    const position = new Map(commits.map((commit, index) => [commit.hash, index]));
    const ordered = [];
    while (ready.length) {
      ready.sort((a, b) => position.get(a.hash) - position.get(b.hash));
      const next = ready.shift();
      ordered.push(next);
      for (const parent of next.parents.filter((hash) => known.has(hash))) {
        children.set(parent, children.get(parent) - 1);
        if (children.get(parent) === 0) ready.push(byHash.get(parent));
      }
    }
    return ordered;
  }

  /* The named tips in claiming order: branches (trunk names first), HEAD, remotes, then tags. */
  function namedTips(snapshot, trunk) {
    const rank = (name) => (trunk.includes(name) ? trunk.indexOf(name) : trunk.length);
    const branchName = (ref) => (ref.kind === "remote" ? ref.name.slice(ref.name.indexOf("/") + 1) : ref.name);
    const tips = (kind) => snapshot.refs
      .filter((ref) => ref.kind === kind)
      .sort((a, b) => rank(branchName(a)) - rank(branchName(b)) || a.name.localeCompare(b.name))
      .map((ref) => ref.target);
    return [...tips("branch"), snapshot.head, ...tips("remote"), ...tips("tag")];
  }

  /* First-parent lines: each tip claims commits down its first parents until one is claimed.
     Named tips claim first; then every commit left (history of merged branches whose name is gone). */
  function linesOf(byHash, named, ordered) {
    const owner = new Map();
    const lines = [];
    const tips = [...named.map((hash) => ({ hash, named: true })), ...ordered.map((commit) => ({ hash: commit.hash, named: false }))];
    for (const { hash: tip, named: isNamed } of tips) {
      if (!byHash.has(tip) || owner.has(tip)) continue;
      const hashes = [];
      let at = tip;
      while (byHash.has(at) && !owner.has(at)) {
        owner.set(at, lines.length);
        hashes.push(at);
        at = byHash.get(at).parents[0];
      }
      lines.push({ hashes, joins: at, named: isNamed });
    }
    return { lines, owner };
  }

  /* The rows each line's lane is busy: its commits, the edge down to the commit it started
     from, and the edges coming in from the merges that took it. A named line keeps its lane up
     to the top, so no other commit is ever drawn above a branch's tip in its lane. */
  function spans(lines, owner, rows, byHash) {
    const busy = lines.map((line) => {
      const top = line.named ? 0 : rows.get(line.hashes[0]);
      const last = rows.get(line.hashes[line.hashes.length - 1]);
      const bottom = line.joins === undefined ? last : rows.has(line.joins) ? Math.max(last, rows.get(line.joins) - 1) : last + 1;
      return { top, bottom };
    });
    for (const [hash, row] of rows) {
      const merged = byHash.get(hash).parents.slice(1).filter((parent) => rows.has(parent));
      for (const parent of merged) busy[owner.get(parent)].top = Math.min(busy[owner.get(parent)].top, row + 1);
      if (merged.length) busy[owner.get(hash)].bottom = Math.max(busy[owner.get(hash)].bottom, row + 1);
    }
    return busy;
  }

  /* The first free lane for each line, in claiming order. */
  function lanesFor(busy) {
    const taken = [];
    return busy.map((span) => {
      const overlaps = (other) => other.top <= span.bottom && span.top <= other.bottom;
      let lane = 0;
      while ((taken[lane] || []).some(overlaps)) lane += 1;
      taken[lane] = [...(taken[lane] || []), span];
      return lane;
    });
  }

  function edgePath(kind, from, to, sizes) {
    const half = sizes.row / 2;
    if (kind === "cut") return `M${from.x},${from.y} L${from.x},${from.y + sizes.row * 0.7}`;
    if (from.x === to.x) return `M${from.x},${from.y} L${to.x},${to.y}`;
    if (kind === "merge") {
      const bend = from.y + sizes.row;
      return `M${from.x},${from.y} C${from.x},${from.y + half} ${to.x},${bend - half} ${to.x},${bend} L${to.x},${to.y}`;
    }
    const bend = to.y - sizes.row;
    return `M${from.x},${from.y} L${from.x},${bend} C${from.x},${bend + half} ${to.x},${to.y - half} ${to.x},${to.y}`;
  }

  function edgesOf(placed, theme) {
    const at = new Map(placed.map((commit) => [commit.hash, commit]));
    const edges = [];
    for (const commit of placed) {
      commit.parents.forEach((parent, index) => {
        const target = at.get(parent);
        const kind = !target ? "cut" : index > 0 ? "merge" : target.lane === commit.lane ? "line" : "fork";
        const laneOwner = kind === "merge" ? target : commit;
        edges.push({ from: commit.hash, to: parent, kind, lane: laneOwner.lane, d: edgePath(kind, commit, target, theme.sizes) });
      });
    }
    return edges;
  }

  /* The labels of one commit: HEAD's marker, then its branch, other branches, remotes and tags. */
  function labelsOf(commit, snapshot, theme, showHead) {
    const { words, sizes } = theme;
    const here = snapshot.refs.filter((ref) => ref.target === commit.hash);
    const current = (ref) => ref.kind === "branch" && ref.name === snapshot.branch && showHead;
    const kinds = ["branch", "remote", "tag"];
    const sorted = here.sort((a, b) => kinds.indexOf(a.kind) - kinds.indexOf(b.kind) || current(b) - current(a) || a.name.localeCompare(b.name));
    const labels = sorted.map((ref) => ({ kind: ref.kind, text: ref.name, current: current(ref) }));
    if (showHead && snapshot.head === commit.hash) labels.unshift({ kind: "head", text: snapshot.branch ? words.head : words.detachedHead, current: false });
    return labels.map((label) => ({ ...label, width: Math.ceil(label.text.length * sizes.char + 2 * sizes.chipPad) }));
  }

  function shorten(text, limit) {
    return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
  }

  /* Where everything goes. options: theme, previous (a Set of the hashes drawn last time, to mark
     new commits), showHead (false for a repository the player is not in, such as the stand-in GitHub). */
  function layout(snapshot, options = {}) {
    const theme = options.theme || DEFAULT_THEME;
    const showHead = options.showHead !== false;
    const { sizes } = theme;
    const ordered = order(snapshot.commits);
    const rows = new Map(ordered.map((commit, index) => [commit.hash, index]));
    const byHash = new Map(ordered.map((commit) => [commit.hash, commit]));
    const { lines, owner } = linesOf(byHash, namedTips(snapshot, theme.trunk), ordered);
    const lanes = lanesFor(spans(lines, owner, rows, byHash));
    const laneCount = lanes.length ? Math.max(...lanes) + 1 : 0;
    const textStart = sizes.pad + laneCount * sizes.lane + sizes.gap;
    const commits = ordered.map((commit, row) => {
      const lane = lanes[owner.get(commit.hash)];
      const labels = labelsOf(commit, snapshot, theme, showHead);
      const subject = shorten(commit.subject, sizes.subject);
      const labelsWidth = labels.reduce((sum, label) => sum + label.width + sizes.chipPad, 0);
      const textEnd = Math.ceil(textStart + labelsWidth + (commit.short.length + 1 + subject.length) * sizes.char);
      return {
        ...commit,
        subject,
        fullSubject: commit.subject,
        row,
        lane,
        x: sizes.pad + lane * sizes.lane + sizes.lane / 2,
        y: sizes.pad + row * sizes.row + sizes.row / 2,
        labels,
        isHead: showHead && snapshot.head === commit.hash,
        isNew: Boolean(options.previous) && !options.previous.has(commit.hash),
        isMerge: commit.parents.length > 1,
        textEnd,
      };
    });
    return {
      commits,
      edges: edgesOf(commits, theme),
      lanes: laneCount,
      textStart,
      width: Math.max(...commits.map((commit) => commit.textEnd), textStart) + sizes.pad,
      height: 2 * sizes.pad + commits.length * sizes.row,
    };
  }

  /* Short sentences about the repository that the graph cannot show. */
  function notes(snapshot, options = {}) {
    const { words } = options.theme || DEFAULT_THEME;
    return [
      snapshot.operation && words.operation(snapshot.operation),
      snapshot.stash > 0 && words.stash(snapshot.stash),
      snapshot.truncated && words.truncated(snapshot.commits.length),
      snapshot.exists && snapshot.head === null && snapshot.branch && snapshot.commits.length > 0 && words.unborn(snapshot.branch),
    ].filter(Boolean);
  }

  const laneColor = (theme, lane) => theme.colors.lanes[lane % theme.colors.lanes.length];

  function tooltip(commit) {
    const when = new Date(commit.time * 1000).toLocaleString();
    return svg("title", {}, `${commit.hash}\n${commit.fullSubject}\n${commit.author}, ${when}`);
  }

  function commitRow(commit, map, theme) {
    const { sizes } = theme;
    let x = map.textStart;
    const chips = commit.labels.map((label) => {
      const chip = theme.shapes.label({ label, x, y: commit.y, color: label.kind === "head" ? theme.colors.head : theme.colors[label.kind], theme });
      x += label.width + sizes.chipPad;
      return chip;
    });
    const classes = ["map-commit", commit.isHead && "is-head", commit.isNew && "is-new", commit.isMerge && "is-merge"].filter(Boolean).join(" ");
    return svg("g", { class: classes, "data-hash": commit.hash },
      tooltip(commit),
      theme.shapes.commit({ ...commit, color: laneColor(theme, commit.lane), theme }),
      chips,
      svg("text", { class: "map-hash", x, y: commit.y, "dominant-baseline": "central" }, commit.short),
      svg("text", { class: "map-subject", x: x + (commit.short.length + 1) * sizes.char, y: commit.y, "dominant-baseline": "central" }, commit.subject),
    );
  }

  function graph(snapshot, map, theme) {
    const head = map.commits.find((commit) => commit.isHead);
    const label = theme.words.summary({ count: map.commits.length, head: head && head.short, branch: snapshot.branch });
    return svg("svg", { class: "map-graph", role: "img", "aria-label": label, width: map.width, height: map.height, viewBox: `0 0 ${map.width} ${map.height}` },
      svg("g", { class: "map-edges" }, map.edges.map((edge) => theme.shapes.edge({ edge, color: laneColor(theme, edge.lane), theme }))),
      svg("g", { class: "map-commits" }, map.commits.map((commit) => commitRow(commit, map, theme))),
    );
  }

  /* One line under the graph: the theme's own HEAD mark and what it means. */
  function key({ snapshot, theme }) {
    const { sizes, words } = theme;
    const half = sizes.radius + 7;
    return el("p", { class: "map-key" },
      svg("svg", { width: 2 * half, height: 2 * half, viewBox: `0 0 ${2 * half} ${2 * half}`, "aria-hidden": "true" },
        theme.shapes.commit({ x: half, y: half, color: laneColor(theme, 0), theme, isHead: true, isNew: false, isMerge: false }),
      ),
      snapshot.branch ? words.here : words.hereDetached,
    );
  }

  function emptyText(snapshot, words) {
    if (!snapshot.exists) return words.noRepository;
    return snapshot.branch ? words.unborn(snapshot.branch) : words.noCommits;
  }

  /* The commit graph as a figure, with its key and notes; a sentence instead when there is nothing to draw. */
  function render(snapshot, options = {}) {
    const theme = options.theme || DEFAULT_THEME;
    const map = snapshot.commits.length ? layout(snapshot, options) : null;
    const headShown = map && map.commits.some((commit) => commit.isHead);
    return el("figure", { class: "repo-map" },
      map ? graph(snapshot, map, theme) : el("p", { class: "map-empty" }, emptyText(snapshot, theme.words)),
      headShown && theme.shapes.key({ snapshot, map, theme }),
      notes(snapshot, { theme }).map((note) => el("p", { class: "map-note" }, note)),
    );
  }

  /* A file in each area as the server classified it (FileEntry's index_change and folder_change,
     git status's two columns): an area is shown where the file is, or where git says it went.
     A conflicted file's change is "conflicted", in the staging area, where git keeps its
     unmerged versions. `changed` is false when git status would not list the file. */
  function areaRow(file) {
    const { path, head, index, folder, conflicted } = file;
    const indexChange = conflicted ? "conflicted" : file.index_change;
    const folderChange = file.folder_change;
    return {
      path,
      folder: folder !== null || folderChange !== null ? { blob: folder, change: folderChange } : null,
      index: index !== null || indexChange !== null ? { blob: index, change: indexChange } : null,
      head: head !== null ? { blob: head, change: null } : null,
      changed: indexChange !== null || (folderChange !== null && folderChange !== "ignored"),
      repository: file.repository,
    };
  }

  const areaRows = (files) => files.map(areaRow);

  /* A hue from the first hex digits of a blob id, so the same content always looks the same. */
  const blobHue = (blob) => parseInt(blob.slice(0, 6), 16) % 360;

  /* One area of a file: its blob, and the change git lists there in the theme's words (`said`
     is the area's part of words.states, none for the last commit). */
  function areaCell(cell, area, said) {
    if (!cell) return el("span", { class: "areas-cell is-absent", role: "cell" }, el("span", { class: "sr-only" }, "absent"));
    return el("span", { class: `areas-cell in-${area}`, role: "cell", "data-change": cell.change },
      cell.blob && el("i", { class: "blob-dot", style: `--hue: ${blobHue(cell.blob)}`, "aria-hidden": "true" }),
      cell.blob && el("code", { title: cell.blob }, cell.blob.slice(0, 7)),
      cell.change && el("em", {}, said[cell.change]),
    );
  }

  function areaLine(row, words) {
    const classes = ["areas-row", row.changed && "is-changed", row.repository && "is-repository"].filter(Boolean).join(" ");
    return el("div", { class: classes, role: "row" },
      el("span", { class: "areas-path", role: "rowheader" },
        el("span", { class: "areas-name", title: row.path }, row.path),
        row.repository && el("span", { class: "areas-repo" }, words.areas.repository),
      ),
      areaCell(row.folder, "folder", words.states.folder),
      el("span", { class: "areas-gap", "aria-hidden": "true" }),
      areaCell(row.index, "index", words.states.index),
      el("span", { class: "areas-gap", "aria-hidden": "true" }),
      areaCell(row.head, "head", {}),
    );
  }

  /* The three areas strip: one line per file, unchanged files folded away when there are many. */
  function renderAreas(files, options = {}) {
    const { words } = options.theme || DEFAULT_THEME;
    const labels = words.areas;
    const rows = areaRows(files);
    const unchanged = rows.filter((row) => !row.changed);
    const fold = unchanged.length > FOLD_UNCHANGED;
    const shown = fold ? rows.filter((row) => row.changed) : rows;
    const strip = el("div", { class: "areas", role: "table", "aria-label": `${labels.folder}, ${labels.index}, ${labels.head}` },
      el("div", { class: "areas-row areas-head", role: "row" },
        el("span", { role: "columnheader" }, labels.file),
        el("span", { role: "columnheader" }, labels.folder),
        el("span", { class: "areas-step", "aria-hidden": "true" }, labels.add, " →"),
        el("span", { role: "columnheader" }, labels.index),
        el("span", { class: "areas-step", "aria-hidden": "true" }, labels.commit, " →"),
        el("span", { role: "columnheader" }, labels.head),
      ),
      shown.map((row) => areaLine(row, words)),
      !rows.length && el("p", { class: "areas-empty" }, labels.empty),
    );
    if (fold) {
      const more = el("div", { class: "areas-row areas-fold", role: "row" },
        el("span", { role: "cell" }, labels.unchanged(unchanged.length), " ",
          el("button", { type: "button", class: "link-button", onclick: () => more.replaceWith(...unchanged.map((row) => areaLine(row, words))) }, labels.show),
        ),
      );
      strip.append(more);
    }
    return strip;
  }

  /* The object database as a table: type, hash and size; objects not in `options.previous` are marked new. */
  function renderObjects(objects, options = {}) {
    const words = (options.theme || DEFAULT_THEME).words.objects;
    if (!objects.length) return el("p", { class: "objects-empty" }, words.empty);
    const isNew = (object) => Boolean(options.previous) && !options.previous.has(object.hash);
    return el("table", { class: "objects" },
      el("thead", {}, el("tr", {}, el("th", { scope: "col" }, words.type), el("th", { scope: "col" }, words.hash), el("th", { scope: "col", class: "num" }, words.size))),
      el("tbody", {}, objects.map((object) => el("tr", { class: isNew(object) ? "is-new" : null },
        el("td", {}, el("span", { class: `object-type is-${object.type}` }, object.type)),
        el("td", {}, el("code", {}, el("b", {}, object.hash.slice(0, 7)), object.hash.slice(7))),
        el("td", { class: "num" }, words.bytes(object.size)),
      ))),
    );
  }

  return { DEFAULT_THEME, theme: themeWith, svg, order, layout, notes, render, areaRows, blobHue, renderAreas, renderObjects };
})();
