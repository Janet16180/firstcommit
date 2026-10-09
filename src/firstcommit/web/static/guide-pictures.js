"use strict";

/*
 * The field guide cards' small pictures, in the look of the game's teaching pictures
 * (docs/drafts/teaching-pictures.md): the desk (Git's places with the files in them) and the
 * chain (commits newest first, each joined to its parents, with name tags and HEAD). The chain
 * is drawn with chain.js's layout, wires and lanes, in its classes, so the game has one chain
 * renderer; only the rows' words are the cards' own (a lit name, a name taken off, a merge
 * commit's mark, your bookmark and the mothership as one name).
 * Every word comes from `words` (GuideText.pictures localized, plus `places`, each place's
 * label); a file's state is written beside it and each commit row says whose it is to a screen
 * reader, so colour is never the only clue. Needs dom.js and chain.js (with strings.js and
 * places.js); orbit.css and guide.css style it. Defines one
 * global, GuidePictures.
 *
 * draw(model, words, {lines}) {element}: model is a desk or a chain as GuideText describes them;
 *   another kind throws a RangeError. Gold means what the command changed and nothing else: a
 *   fresh chip, place, commit (with its lines to its parents) or name, a name taken off (`gone`),
 *   and the HEAD mark when only HEAD moved (`moved`). A commit to look at (`look`) gets a violet
 *   ring instead. With `lines` (git log --graph's output lines), a chain's rows follow git's: one
 *   per line, in git's order, each commit on the line that ends with its subject and a connector
 *   line (|/ or |\) an empty row the wires pass through; a line with a hash that matches no
 *   commit throws a RangeError.
 */

/* global Dom, Chain */
/* exported GuidePictures */

const GuidePictures = (function () {
  const { el } = Dom;
  const PLACES = ["folder", "staging", "vault", "remote"];
  const fresh = (item, base) => (item.fresh ? `${base} gp-fresh` : base);

  function chip(item, words) {
    const said = item.left ? words.left : item.state ? words.states[item.state] : null;
    const state = said ? el("span", { class: "gp-state" }, said) : null;
    return el("li", { class: fresh(item, `gp-chip gp-chip--${item.state || "plain"}${item.left ? " gp-left" : ""}`) }, el("span", { class: "gp-file" }, item.name), state);
  }

  function place(key, items, lit, words) {
    const absent = items === null;
    const body = absent
      ? el("p", { class: "gp-none" }, words.notYet)
      : items.length === 0
        ? el("p", { class: "gp-none" }, words.empty)
        : el("ul", { class: "gp-chips", role: "list" }, items.map((item) => chip(item, words)));
    return el("section", { class: `gp-place gp-place--${key}${absent ? " gp-place--absent" : ""}${lit ? " gp-fresh" : ""}` },
      el("h4", { class: "gp-place-name" }, words.places[key]),
      body);
  }

  function desk(model, words) {
    return el("div", { class: "gp gp-desk" },
      PLACES.filter((key) => key in model).map((key) => place(key, model[key], (model.fresh || []).includes(key), words)),
      model.note ? el("p", { class: "gp-note" }, words.notes[model.note]) : null);
  }

  /* Each commit's lines are styled by the commit: lit when the command made it, faded for a
     ghost, pink dotted for the mothership's alone. */
  const lineStyle = (commit) => (commit.fresh ? "fresh" : commit.ghost ? "ghost" : commit.who === "mothership" ? "mothership" : null);
  const rowKind = (commit) => (commit.ghost ? "is-ghost" : commit.who === "mothership" ? "is-mothership-only" : null);

  const headMark = (words, lit = false) => el("span", { class: lit ? "chain-head gp-fresh" : "chain-head", title: words.head }, "HEAD \u25B6");
  const TAG = { branch: "chain-tag", head: "chain-tag is-head", remote: "chain-tag is-bookmark" };
  const tag = (name, kind, text = name.name) => el("span", { class: fresh(name, TAG[kind]) }, text);

  /* A name the command took off: struck through and lit, with the words that say so. */
  function goneTag(name, words) {
    return el("span", { class: "gp-gone" }, el("s", { class: "chain-tag gp-fresh" }, name.name), el("span", { class: "gp-gone-note" }, words.gone));
  }

  /* The row's names, in chain.js's look. Where your bookmark and the mothership's pin sit on one
     commit they are one name, "origin/main (mothership)", lit if either moved; apart, the
     mothership is a pin. */
  function rowNames(names, head, moved, words) {
    const pin = names.find((name) => name.kind === "mothership");
    const bookmark = names.find((name) => name.kind === "remote");
    return names.map((name) => {
      if (name.gone) return goneTag(name, words);
      if (name.name === head) return [headMark(words, moved || name.fresh), tag(name, "head")];
      if (name === pin) return bookmark ? null : el("span", { class: fresh(name, "chain-pin is-mothership") }, words.mothership);
      if (name === bookmark && pin) return el("span", { class: fresh({ fresh: name.fresh || pin.fresh }, "chain-tag is-bookmark gp-synced") }, `${name.name} (${words.mothership})`);
      return tag(name, name.kind);
    });
  }

  function commitRow({ commit, column }, pieces, columns, model, words) {
    const who = commit.ghost ? words.ghost : commit.who === "mothership" ? words.notYours : words.by[commit.who || "you"];
    const cap = el("span", { class: ["chain-cap", rowKind(commit)].filter(Boolean).join(" ") });
    cap.style.setProperty("--column", String(column));
    const kinds = ["chain-row", rowKind(commit), commit.fresh && "is-look", commit.look && "gp-look", commit.faint && "gp-faint"];
    return el("li", { class: kinds.filter(Boolean).join(" "), "data-hash": commit.id },
      el("span", { class: "chain-lanes" }, Chain.lane(pieces, columns, 0), cap),
      el("span", { class: "chain-body" },
        el("span", { class: "gp-sr" }, who),
        model.head === commit.id ? headMark(words, model.moved) : null,
        rowNames(model.names.filter((name) => name.on === commit.id), model.head, model.moved, words),
        commit.subject ? el("em", { class: "gp-subject" }, commit.subject) : null,
        commit.mark ? el("span", { class: "gp-mark" }, words.marks[commit.mark]) : null,
        commit.note ? el("span", { class: "gp-note" }, words.notes[commit.note]) : null));
  }

  /* A row for a line of git's graph that holds no commit (|/ or |\): only the wires that cross
     from the commit row above it to the one below. */
  function connector(above, columns) {
    const crossing = above.filter((piece) => ["bottom", "out", "full"].includes(piece.shape)).map((piece) => {
      const column = piece.shape === "out" ? piece.to : piece.from;
      return { ...piece, shape: "full", from: column, to: column };
    });
    return el("li", { class: "chain-row gp-connector", "aria-hidden": "true" }, el("span", { class: "chain-lanes" }, Chain.lane(crossing, columns, 0)));
  }

  const HASH = /\b[0-9a-f]{7,}\b/;

  /* The rows in the order of git's lines: the row whose subject ends each line, or null for a
     line that holds no commit. */
  function inGitOrder(rows, lines) {
    return lines.map((line) => {
      const found = rows.find((placed) => placed.commit.subject && line.endsWith(` ${placed.commit.subject}`));
      if (!found && HASH.test(line)) throw new RangeError(`no commit in the picture for: ${line}`);
      return found || null;
    });
  }

  /* The chain as chain.js lays it out and wires it, main's line in the first column (else
     HEAD's), with the card's own row words; in git's order when it goes beside git's lines. */
  function chain(model, words, lines) {
    const commits = model.commits.map((commit, at) => ({ ...commit, hash: commit.id, time: model.commits.length - at }));
    const main = model.names.find((name) => name.kind === "branch" && name.name === "main" && !name.gone);
    const headBranch = model.names.find((name) => name.kind === "branch" && name.name === model.head);
    const trunk = main ? main.on : headBranch ? headBranch.on : model.head;
    const layout = Chain.layout(commits, [trunk]);
    const { columns } = layout;
    const placed = lines ? inGitOrder(layout.rows, lines) : layout.rows;
    const rows = placed.filter(Boolean);
    const styles = new Map(commits.filter(lineStyle).map((commit) => [commit.hash, lineStyle(commit)]));
    const pieces = Chain.wires(rows, styles);
    let drawn = -1;
    const items = placed.map((row) => {
      if (!row) return connector(pieces[drawn], columns);
      drawn += 1;
      return commitRow(row, pieces[drawn], columns, model, words);
    });
    const element = el("div", { class: "gp gp-chain chain" },
      el("ol", { class: "chain-rows", role: "list" }, items));
    element.style.setProperty("--columns", String(columns));
    element.style.setProperty("--column-width", `${Chain.COLUMN}px`);
    return element;
  }

  const KINDS = { desk, chain };

  function draw(model, words, { lines = null } = {}) {
    if (!(model.kind in KINDS)) throw new RangeError(`no picture of kind ${model.kind}`);
    return KINDS[model.kind](model, words, lines);
  }

  return { draw };
})();
