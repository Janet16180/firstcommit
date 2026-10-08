"use strict";

/*
 * The chain (docs/drafts/teaching-pictures.md): every commit drawn once, newest at the top, each
 * joined to its parents, and a side line in a column of its own for each branch that splits off,
 * as git draws `--graph`. On it, the project's names: the branch HEAD rides is a filled tag behind
 * the HEAD mark, other branches are outlined, origin/* are dashed (your bookmark of where the
 * mothership was). Pins mark where the mothership's and Alex's branches really are; the
 * mothership's commits you lack are pink dotted, and a commit no name leads to is a faded, dashed
 * ghost. A gold ring means "look here" and nothing else. Needs dom.js, strings.js and places.js. Defines one
 * global, Chain.
 *
 * layout(commits, trunk) {rows: [{commit, column}], columns}: the commits, newest generation
 *   first, each side line kept just above the commit it leaves. Column 0 holds the first-parent
 *   chains of the `trunk` hashes; every other line takes the next free column.
 * wires(rows, styles, walk) [[{shape, from, to, style, step}]]: each row's wire pieces. "full"
 *   crosses the row, "top" and "bottom" end at its capsule, "in" turns from a side column at the
 *   top into the capsule's, "out" leaves the capsule for a side column at the bottom. `styles`
 *   maps a child's hash to the look of its lines ("ghost", "mothership"); `walk` lists hashes
 *   whose links light up in turn ("walk", with the link's step).
 * create() {element, update(view)}: view = {project, github, teammate, ghosts, show: {mothership,
 *   alex, ghosts}, look: [subject | "HEAD"], walk, placed, legend}. A revert's gold arc runs in a
 *   margin left of the lanes, from its capsule down to the commit it undoes (found by the
 *   subject git gives a revert), and both rows say so. main's line (else origin/main's,
 *   else HEAD's) holds the first column. `walk` lights git log's path
 *   from HEAD; `placed` names get a tick (the captain's chart); `legend: false` leaves the key
 *   out. `plain` draws the capsules alone, with no name, HEAD mark, pin or key (the vault's column
 *   before the chain is born); `touched` (hashes, or null) dims every other commit. `owner` ("you" unless "alex") says whose repository `project` is, for its colour; the
 *   other person's pins (show.alex, `teammate`) are then yours. `whatif` (names) draws the WHAT IF: greyscale under its heading, the chain without those
 *   names, the commits only they reached as ghosts. An update that brings nothing new keeps the
 *   drawing, so its motions are not started over.
 */

/* global Dom, Strings, Places */
/* exported Chain */

const Chain = (function () {
  const { el, svg } = Dom;
  const { t } = Strings;
  /* A lane's geometry, in the units of its viewBox: the first column's x, the step between
     columns, and the row's height, which the lane stretches to fit. */
  const X0 = 10;
  const COLUMN = 28;
  const HEIGHT = 100;
  /* A revert's arc runs in a margin left of the first column, at ARC. */
  const MARGIN = 14;
  const ARC = -7;
  const REVERT = /^Revert "(.+)"$/;

  function layout(commits, trunk) {
    const byHash = new Map(commits.map((commit) => [commit.hash, commit]));
    const generations = new Map();
    const generation = (hash) => {
      if (!generations.has(hash)) {
        const parents = byHash.get(hash).parents.filter((parent) => byHash.has(parent));
        generations.set(hash, parents.length ? 1 + Math.max(...parents.map(generation)) : 0);
      }
      return generations.get(hash);
    };
    const sorted = [...commits].sort((a, b) => generation(b.hash) - generation(a.hash) || b.time - a.time || (a.hash < b.hash ? -1 : 1));
    const onTrunk = new Set();
    for (const tip of trunk) {
      for (let at = tip; at && byHash.has(at) && !onTrunk.has(at); at = byHash.get(at).parents[0]) onTrunk.add(at);
    }
    const side = sorted.filter((commit) => !onTrunk.has(commit.hash));
    const forkOf = (commit) => {
      let at = commit;
      while (at && !onTrunk.has(at.hash)) at = byHash.get(at.parents[0]);
      return at ? at.hash : null;
    };
    const grouped = [];
    for (const commit of sorted.filter((each) => onTrunk.has(each.hash))) grouped.push(...side.filter((each) => forkOf(each) === commit.hash), commit);
    grouped.push(...side.filter((each) => !grouped.includes(each)));
    /* A side commit takes the column of its side child, so a line stays straight; a new line takes
       the next free column, so two branches off one commit never share one. */
    const columns = new Map([...onTrunk].map((hash) => [hash, 0]));
    let next = 1;
    for (const commit of grouped.filter((each) => !onTrunk.has(each.hash))) {
      const child = grouped.find((each) => !onTrunk.has(each.hash) && each.parents[0] === commit.hash && columns.has(each.hash));
      columns.set(commit.hash, child ? columns.get(child.hash) : next++);
    }
    return { rows: grouped.map((commit) => ({ commit, column: columns.get(commit.hash) })), columns: next };
  }

  /* Each revert and the commit it undoes, found by the subject git gives a revert, as row pairs. */
  function undoings(rows) {
    return rows.flatMap((row, top) => {
      const undone = REVERT.exec(row.commit.subject);
      const bottom = undone ? rows.findIndex((each, at) => at > top && each.commit.subject === undone[1]) : -1;
      return bottom > top ? [[top, bottom]] : [];
    });
  }

  function wires(rows, styles, walk = [], undone = []) {
    const index = new Map(rows.map((row, at) => [row.commit.hash, at]));
    const pieces = rows.map(() => []);
    const link = (top, bottom, style, step = null) => {
      const from = rows[top].column;
      const to = rows[bottom].column;
      const through = from > to ? from : to;
      const piece = (shape, a, b) => ({ shape, from: a, to: b, style, step });
      pieces[top].push(from < to ? piece("out", from, to) : piece("bottom", from, from));
      for (let row = top + 1; row < bottom; row += 1) pieces[row].push(piece("full", through, through));
      pieces[bottom].push(from > to ? piece("in", from, to) : piece("top", to, to));
    };
    rows.forEach((row, top) => {
      for (const parent of row.commit.parents) {
        if (index.get(parent) > top) link(top, index.get(parent), styles.get(row.commit.hash) || "line");
      }
    });
    walk.slice(1).forEach((hash, step) => {
      if (index.has(walk[step]) && index.has(hash)) link(index.get(walk[step]), index.get(hash), "walk", step);
    });
    for (const [top, bottom] of undone) {
      const arc = (shape, column) => ({ shape, from: column, to: column, style: "undo", step: null });
      pieces[top].push(arc("undo-out", rows[top].column));
      for (let row = top + 1; row < bottom; row += 1) pieces[row].push(arc("undo-full", 0));
      pieces[bottom].push(arc("undo-in", rows[bottom].column));
    }
    return pieces;
  }

  const x = (column) => X0 + column * COLUMN;
  const PATHS = {
    full: (a) => `M${x(a)} 0 L${x(a)} ${HEIGHT}`,
    top: (a) => `M${x(a)} 0 L${x(a)} ${HEIGHT / 2}`,
    bottom: (a) => `M${x(a)} ${HEIGHT / 2} L${x(a)} ${HEIGHT}`,
    in: (a, b) => `M${x(a)} 0 L${x(b)} ${HEIGHT / 2}`,
    out: (a, b) => `M${x(a)} ${HEIGHT / 2} L${x(b)} ${HEIGHT}`,
    "undo-out": (a) => `M${x(a) - 9} ${HEIGHT / 2} L${ARC} ${HEIGHT / 2} L${ARC} ${HEIGHT}`,
    "undo-full": () => `M${ARC} 0 L${ARC} ${HEIGHT}`,
    "undo-in": (a) => `M${ARC} 0 L${ARC} ${HEIGHT / 2} L${x(a) - 9} ${HEIGHT / 2} M${x(a) - 15} ${HEIGHT / 2 - 7} L${x(a) - 9} ${HEIGHT / 2} L${x(a) - 15} ${HEIGHT / 2 + 7}`,
  };

  function lane(pieces, columns, margin) {
    const width = 2 * X0 + (columns - 1) * COLUMN;
    return svg("svg", { class: "chain-lane", viewBox: `${-margin} 0 ${width + margin} ${HEIGHT}`, preserveAspectRatio: "none", "aria-hidden": "true" },
      ...pieces.map((piece) => {
        const path = svg("path", { class: `chain-wire is-${piece.style}`, d: PATHS[piece.shape](piece.from, piece.to), "vector-effect": "non-scaling-stroke" });
        if (piece.step !== null) path.style.setProperty("--step", String(piece.step));
        return path;
      }));
  }

  const RANK = { head: 0, branch: 1, tag: 2, remote: 3 };

  function tags(project, hash, lookAtHead, placed) {
    const head = () => el("span", { class: lookAtHead ? "chain-head is-look" : "chain-head", title: t("chain.headTip") }, "HEAD ▶");
    const kindOf = (ref) => (ref.kind === "branch" && ref.name === project.branch ? "head" : ref.kind);
    const named = project.refs.filter((ref) => ref.target === hash).sort((a, b) => RANK[kindOf(a)] - RANK[kindOf(b)]);
    const parts = named.flatMap((ref) => {
      const kind = kindOf(ref);
      const kinds = { head: "chain-tag is-head", branch: "chain-tag", tag: "chain-tag is-tag", remote: "chain-tag is-bookmark" }[kind];
      const tag = el("span", { class: placed.includes(ref.name) ? `${kinds} is-placed` : kinds }, ref.name);
      return kind === "head" ? [head(), tag] : [tag];
    });
    return project.branch === null && project.head === hash ? [head(), ...parts] : parts;
  }

  /* kind: "mothership", or the other person ("alex" or "you"). */
  function pins(snapshot, hash, kind) {
    if (!snapshot) return [];
    const who = kind === "mothership" ? Places.label("remote") : t(`chain.pin.${kind}`);
    return snapshot.refs.filter((ref) => ref.kind === "branch" && ref.target === hash).map((ref) => el("span", { class: `chain-pin is-${kind}` }, who, `: ${ref.name}`));
  }

  function legend(project, marks) {
    const item = (swatch, key) => el("li", {}, el("span", { class: `${swatch} chain-swatch`, "aria-hidden": "true" }), t(key));
    const kinds = new Set(project.refs.map((ref) => (ref.kind === "branch" && ref.name === project.branch ? "head" : ref.kind)));
    return el("ul", { class: "chain-legend" }, ...[
      kinds.has("head") && item("chain-tag is-head", "chain.key.head"),
      kinds.has("branch") && item("chain-tag", "chain.key.branch"),
      kinds.has("remote") && item("chain-tag is-bookmark", "chain.key.bookmark"),
      marks.mothership && item("chain-pin is-mothership", "chain.key.mothership"),
      marks.other && item(`chain-pin is-${marks.other}`, `chain.key.${marks.other}`),
      item("chain-key-line", "chain.key.line"),
      marks.only && item("chain-cap is-mothership-only", "chain.key.only"),
      marks.ghost && item("chain-cap is-ghost", "chain.key.ghost"),
    ].filter(Boolean));
  }

  /* The pins the chain draws, for its key: the mothership's, and the other person's by who they are. */
  const pinned = (show, github, teammate, other) => ({ mothership: show.mothership && Boolean(github), other: show.alex && Boolean(teammate) && other });

  /* The tip whose first-parent line takes the first column: main's, or a tip further along that
     same line (origin/main or the mothership's main ahead of it, a fast-forward away); without
     main, origin/main's, else HEAD's. */
  function trunkOf(project, byHash, github) {
    const tip = (name, snapshot = project) => (snapshot.refs.find((ref) => ref.name === name) || {}).target;
    const motherMain = github ? tip("main", github) : null;
    const line = (from) => {
      const path = [];
      for (let at = from; at && byHash.has(at) && !path.includes(at); at = byHash.get(at).parents[0]) path.push(at);
      return path;
    };
    const base = tip("main") || tip("origin/main") || project.head;
    const ahead = [tip("origin/main"), motherMain].filter((other) => other && line(other).includes(base));
    return ahead.reduce((best, other) => (line(other).length > line(best).length ? other : best), base);
  }

  /* What a row says about a revert: what it undoes, or that a later commit undid it. */
  function undoNote(rows, undone, at) {
    const pair = undone.find(([top, bottom]) => top === at || bottom === at);
    if (!pair) return null;
    const text = pair[0] === at ? t("chain.undoes", { subject: rows[pair[1]].commit.subject }) : t("chain.undone");
    return el("span", { class: "chain-undo" }, text);
  }

  /* HEAD's commit and its first parents, the path git log walks. */
  function walkFrom(project, byHash) {
    const path = [];
    for (let at = project.head; at && byHash.has(at) && !path.includes(at); at = byHash.get(at).parents[0]) path.push(at);
    return path;
  }

  /* The project as it would be without the names `without`: the commits only they reached are
     then reached by nothing. No names: the project as it is. */
  function pretend(project, without) {
    if (!without) return { project, orphaned: [] };
    const refs = project.refs.filter((ref) => !without.includes(ref.name));
    const byHash = new Map(project.commits.map((commit) => [commit.hash, commit]));
    const reached = new Set();
    const queue = [...refs.map((ref) => ref.target), project.head].filter(Boolean);
    while (queue.length) {
      const hash = queue.pop();
      if (reached.has(hash) || !byHash.has(hash)) continue;
      reached.add(hash);
      queue.push(...byHash.get(hash).parents);
    }
    return { project: { ...project, refs }, orphaned: project.commits.filter((commit) => !reached.has(commit.hash)) };
  }

  function create() {
    const element = el("section", { class: "chain", "aria-label": t("chain.label") });
    let drawnFrom = null;

    function update(view) {
      const key = JSON.stringify([view, Strings.language()]);
      if (key === drawnFrom) return;
      drawnFrom = key;
      draw(view);
    }

    function draw({ project: real, github, teammate, ghosts, show, look, walk, placed = [], legend: keyed = true, whatif = null, owner = "you", plain = false, touched = null }) {
      const other = owner === "alex" ? "you" : "alex";
      const { project, orphaned } = pretend(real, whatif);
      const mine = new Set(project.commits.map((commit) => commit.hash));
      const motherOnly = show.mothership && github ? github.commits.filter((commit) => !mine.has(commit.hash)) : [];
      const lost = show.ghosts ? ghosts.filter((commit) => !mine.has(commit.hash)) : [];
      const commits = [...project.commits, ...motherOnly, ...lost];
      const byHash = new Map(commits.map((commit) => [commit.hash, commit]));
      const styles = new Map([...motherOnly.map((commit) => [commit.hash, "mothership"]), ...[...lost, ...orphaned].map((commit) => [commit.hash, "ghost"])]);
      const trunk = trunkOf(project, byHash, show.mothership ? github : null);
      const { rows, columns } = layout(commits, trunk ? [trunk] : []);
      const undone = undoings(rows);
      const margin = undone.length ? MARGIN : 0;
      const pieces = wires(rows, styles, walk ? walkFrom(project, byHash) : [], undone);
      const looked = new Set(look);
      element.setAttribute("aria-label", t("chain.label"));
      element.dataset.owner = owner;
      element.classList.toggle("is-whatif", Boolean(whatif));
      element.classList.toggle("has-undo", margin > 0);
      element.style.setProperty("--columns", String(columns));
      element.style.setProperty("--column-width", `${COLUMN}px`);
      element.style.setProperty("--margin", `${margin}px`);
      element.replaceChildren(
        ...(whatif ? [el("span", { class: "chain-whatif" }, t("moment.whatIf"))] : []),
        el("ol", { class: "chain-rows" }, ...rows.map((row, at) => {
          const { commit } = row;
          const style = styles.get(commit.hash);
          const kind = { mothership: "is-mothership-only", ghost: "is-ghost" }[style] || "";
          const cap = el("span", { class: `chain-cap ${kind} ${commit.subject.startsWith("Revert ") ? "is-revert" : ""}`.trim() });
          cap.style.setProperty("--column", String(row.column));
          const dim = touched !== null && !touched.includes(commit.hash);
          return el("li", { class: ["chain-row", kind, looked.has(commit.subject) && "is-look", dim && "is-dim"].filter(Boolean).join(" "), "data-hash": commit.hash },
            el("span", { class: "chain-lanes" }, lane(pieces[at], columns, margin), cap),
            el("span", { class: "chain-body" },
              el("code", { class: "chain-hash" }, commit.short),
              el("span", { class: "chain-subject" }, commit.subject),
              style === "mothership" && el("span", { class: "chain-only" }, t("chain.only")),
              undoNote(rows, undone, at),
              ...(plain ? [] : [
                ...tags(project, commit.hash, looked.has("HEAD"), placed),
                ...(show.mothership ? pins(github, commit.hash, "mothership") : []),
                ...(show.alex ? pins(teammate, commit.hash, other) : []),
              ])));
        })),
        ...(keyed && !plain ? [legend(project, { ...pinned(show, github, teammate, other), only: motherOnly.length > 0, ghost: lost.length + orphaned.length > 0 })] : []));
    }

    return { element, update };
  }

  return { create, layout, wires };
})();
