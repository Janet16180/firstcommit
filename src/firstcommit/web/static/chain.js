"use strict";

/*
 * The chain (docs/drafts/teaching-pictures.md): every commit drawn once, newest at the top, each
 * joined to its parents, and a side line in a column of its own for each branch that splits off,
 * as git draws `--graph`. On it, the project's names: the branch HEAD rides is a filled tag behind
 * the HEAD mark, other branches are outlined, origin/* are dashed (your bookmark of where the
 * mothership was). Pins mark where the mothership's and Alex's branches really are; the
 * mothership's commits you lack are pink dotted, and a commit no name leads to is a faded, dashed
 * ghost. A gold ring means "look here" and nothing else. Needs dom.js and strings.js. Defines one
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
 *   alex, ghosts}, look: [subject | "HEAD"], walk}. `walk` lights git log's path from HEAD.
 */

/* global Dom, Strings */
/* exported Chain */

const Chain = (function () {
  const { el, svg } = Dom;
  const { t } = Strings;
  /* A lane's geometry, in the units of its viewBox: the first column's x, the step between
     columns, and the row's height, which the lane stretches to fit. */
  const X0 = 10;
  const COLUMN = 22;
  const HEIGHT = 100;

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

  function wires(rows, styles, walk = []) {
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
    return pieces;
  }

  const x = (column) => X0 + column * COLUMN;
  const PATHS = {
    full: (a) => `M${x(a)} 0 L${x(a)} ${HEIGHT}`,
    top: (a) => `M${x(a)} 0 L${x(a)} ${HEIGHT / 2}`,
    bottom: (a) => `M${x(a)} ${HEIGHT / 2} L${x(a)} ${HEIGHT}`,
    in: (a, b) => `M${x(a)} 0 L${x(b)} ${HEIGHT / 2}`,
    out: (a, b) => `M${x(a)} ${HEIGHT / 2} L${x(b)} ${HEIGHT}`,
  };

  function lane(pieces, columns) {
    const width = 2 * X0 + (columns - 1) * COLUMN;
    return svg("svg", { class: "chain-lane", viewBox: `0 0 ${width} ${HEIGHT}`, preserveAspectRatio: "none", "aria-hidden": "true" },
      ...pieces.map((piece) => {
        const path = svg("path", { class: `chain-wire is-${piece.style}`, d: PATHS[piece.shape](piece.from, piece.to), "vector-effect": "non-scaling-stroke" });
        if (piece.step !== null) path.style.setProperty("--step", String(piece.step));
        return path;
      }));
  }

  const RANK = { head: 0, branch: 1, tag: 2, remote: 3 };

  function tags(project, hash, lookAtHead) {
    const head = () => el("span", { class: lookAtHead ? "chain-head is-look" : "chain-head", title: t("chain.headTip") }, "HEAD ▶");
    const kindOf = (ref) => (ref.kind === "branch" && ref.name === project.branch ? "head" : ref.kind);
    const named = project.refs.filter((ref) => ref.target === hash).sort((a, b) => RANK[kindOf(a)] - RANK[kindOf(b)]);
    const parts = named.flatMap((ref) => {
      const kind = kindOf(ref);
      const tag = el("span", { class: { head: "chain-tag is-head", branch: "chain-tag", tag: "chain-tag is-tag", remote: "chain-tag is-bookmark" }[kind] }, ref.name);
      return kind === "head" ? [head(), tag] : [tag];
    });
    return project.branch === null && project.head === hash ? [head(), ...parts] : parts;
  }

  function pins(snapshot, hash, kind) {
    if (!snapshot) return [];
    return snapshot.refs.filter((ref) => ref.kind === "branch" && ref.target === hash).map((ref) => el("span", { class: `chain-pin is-${kind}` }, t(`chain.pin.${kind}`, { name: ref.name })));
  }

  function legend(project, marks) {
    const item = (swatch, key) => el("li", {}, el("span", { class: `${swatch} chain-swatch`, "aria-hidden": "true" }), t(key));
    const kinds = new Set(project.refs.map((ref) => (ref.kind === "branch" && ref.name === project.branch ? "head" : ref.kind)));
    return el("ul", { class: "chain-legend" }, ...[
      kinds.has("head") && item("chain-tag is-head", "chain.key.head"),
      kinds.has("branch") && item("chain-tag", "chain.key.branch"),
      kinds.has("remote") && item("chain-tag is-bookmark", "chain.key.bookmark"),
      marks.mothership && item("chain-pin is-mothership", "chain.key.mothership"),
      marks.alex && item("chain-pin is-alex", "chain.key.alex"),
      item("chain-key-line", "chain.key.line"),
      marks.only && item("chain-cap is-mothership-only", "chain.key.only"),
      marks.ghost && item("chain-cap is-ghost", "chain.key.ghost"),
    ].filter(Boolean));
  }

  /* HEAD's commit and its first parents, the path git log walks. */
  function walkFrom(project, byHash) {
    const path = [];
    for (let at = project.head; at && byHash.has(at) && !path.includes(at); at = byHash.get(at).parents[0]) path.push(at);
    return path;
  }

  function create() {
    const element = el("section", { class: "chain", "aria-label": t("chain.label") });

    function update({ project, github, teammate, ghosts, show, look, walk }) {
      const mine = new Set(project.commits.map((commit) => commit.hash));
      const motherOnly = show.mothership && github ? github.commits.filter((commit) => !mine.has(commit.hash)) : [];
      const lost = show.ghosts ? ghosts.filter((commit) => !mine.has(commit.hash)) : [];
      const commits = [...project.commits, ...motherOnly, ...lost];
      const byHash = new Map(commits.map((commit) => [commit.hash, commit]));
      const styles = new Map([...motherOnly.map((commit) => [commit.hash, "mothership"]), ...lost.map((commit) => [commit.hash, "ghost"])]);
      const trunk = [...project.refs.filter((ref) => ref.name === "main" || ref.name === "origin/main").map((ref) => ref.target), project.head];
      const { rows, columns } = layout(commits, trunk.filter(Boolean));
      const pieces = wires(rows, styles, walk ? walkFrom(project, byHash) : []);
      const looked = new Set(look);
      element.setAttribute("aria-label", t("chain.label"));
      element.style.setProperty("--columns", String(columns));
      element.replaceChildren(
        el("ol", { class: "chain-rows" }, ...rows.map((row, at) => {
          const { commit } = row;
          const style = styles.get(commit.hash);
          const kind = { mothership: "is-mothership-only", ghost: "is-ghost" }[style] || "";
          const cap = el("span", { class: `chain-cap ${kind} ${commit.subject.startsWith("Revert ") ? "is-revert" : ""}`.trim() });
          cap.style.setProperty("--column", String(row.column));
          return el("li", { class: ["chain-row", kind, looked.has(commit.subject) && "is-look"].filter(Boolean).join(" "), "data-hash": commit.hash },
            el("span", { class: "chain-lanes" }, lane(pieces[at], columns), cap),
            el("span", { class: "chain-body" },
              el("code", { class: "chain-hash" }, commit.short),
              el("span", { class: "chain-subject" }, commit.subject),
              style === "mothership" && el("span", { class: "chain-only" }, t("chain.only")),
              ...tags(project, commit.hash, looked.has("HEAD")),
              ...(show.mothership ? pins(github, commit.hash, "mothership") : []),
              ...(show.alex ? pins(teammate, commit.hash, "alex") : [])));
        })),
        legend(project, { mothership: show.mothership && Boolean(github), alex: show.alex && Boolean(teammate), only: motherOnly.length > 0, ghost: lost.length > 0 }));
    }

    return { element, update };
  }

  return { create, layout, wires };
})();
