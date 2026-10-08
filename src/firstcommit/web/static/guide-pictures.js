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
 * draw(model, words) {element}: model is a desk or a chain as GuideText describes them;
 *   another kind throws a RangeError. What the command changed is lit in gold: a fresh chip,
 *   place, commit (with its lines to its parents) or name, and a name taken off (`gone`).
 */

/* global Dom, Chain */
/* exported GuidePictures */

const GuidePictures = (function () {
  const { el } = Dom;
  const PLACES = ["folder", "staging", "vault", "remote"];
  const fresh = (item, base) => (item.fresh ? `${base} gp-fresh` : base);

  function chip(item, words) {
    const state = item.state ? el("span", { class: "gp-state" }, words.states[item.state]) : null;
    return el("li", { class: fresh(item, `gp-chip gp-chip--${item.state || "plain"}`) }, el("span", { class: "gp-file" }, item.name), state);
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
    return el("div", { class: "gp gp-desk" }, PLACES.filter((key) => key in model).map((key) => place(key, model[key], (model.fresh || []).includes(key), words)));
  }

  /* Each commit's lines are styled by the commit: lit when the command made it, faded for a
     ghost, pink dotted for the mothership's alone. */
  const lineStyle = (commit) => (commit.fresh ? "fresh" : commit.ghost ? "ghost" : commit.who === "mothership" ? "mothership" : null);
  const rowKind = (commit) => (commit.ghost ? "is-ghost" : commit.who === "mothership" ? "is-mothership-only" : null);

  const headMark = (words) => el("span", { class: "chain-head", title: words.head }, "HEAD \u25B6");
  const TAG = { branch: "chain-tag", head: "chain-tag is-head", remote: "chain-tag is-bookmark" };
  const tag = (name, kind, text = name.name) => el("span", { class: fresh(name, TAG[kind]) }, text);

  /* A name the command took off: struck through and lit, with the words that say so. */
  function goneTag(name, words) {
    return el("span", { class: "gp-gone" }, el("s", { class: "chain-tag gp-fresh" }, name.name), el("span", { class: "gp-gone-note" }, words.gone));
  }

  /* The row's names, in chain.js's look. Where your bookmark and the mothership's pin sit on one
     commit they are one name, "origin/main (mothership)", lit if either moved; apart, the
     mothership is a pin. */
  function rowNames(names, head, words) {
    const pin = names.find((name) => name.kind === "mothership");
    const bookmark = names.find((name) => name.kind === "remote");
    return names.map((name) => {
      if (name.gone) return goneTag(name, words);
      if (name.name === head) return [headMark(words), tag(name, "head")];
      if (name === pin) return bookmark ? null : el("span", { class: fresh(name, "chain-pin is-mothership") }, words.mothership);
      if (name === bookmark && pin) return el("span", { class: fresh({ fresh: name.fresh || pin.fresh }, "chain-tag is-bookmark gp-synced") }, `${name.name} (${words.mothership})`);
      return tag(name, name.kind);
    });
  }

  function commitRow({ commit, column }, pieces, columns, model, words) {
    const who = commit.ghost ? words.ghost : commit.who === "mothership" ? words.notYours : words.by[commit.who || "you"];
    const cap = el("span", { class: ["chain-cap", rowKind(commit)].filter(Boolean).join(" ") });
    cap.style.setProperty("--column", String(column));
    return el("li", { class: ["chain-row", rowKind(commit), commit.fresh && "is-look"].filter(Boolean).join(" "), "data-hash": commit.id },
      el("span", { class: "chain-lanes" }, Chain.lane(pieces, columns, 0), cap),
      el("span", { class: "chain-body" },
        el("span", { class: "gp-sr" }, who),
        model.head === commit.id ? headMark(words) : null,
        rowNames(model.names.filter((name) => name.on === commit.id), model.head, words),
        commit.mark ? el("span", { class: "gp-mark" }, words.marks[commit.mark]) : null));
  }

  /* The chain as chain.js lays it out and wires it, main's line in the first column (else
     HEAD's), with the card's own row words. */
  function chain(model, words) {
    const commits = model.commits.map((commit, at) => ({ ...commit, hash: commit.id, time: model.commits.length - at }));
    const main = model.names.find((name) => name.kind === "branch" && name.name === "main" && !name.gone);
    const headBranch = model.names.find((name) => name.kind === "branch" && name.name === model.head);
    const trunk = main ? main.on : headBranch ? headBranch.on : model.head;
    const { rows, columns } = Chain.layout(commits, [trunk]);
    const styles = new Map(commits.filter(lineStyle).map((commit) => [commit.hash, lineStyle(commit)]));
    const pieces = Chain.wires(rows, styles);
    const element = el("div", { class: "gp gp-chain chain" },
      el("ol", { class: "chain-rows", role: "list" }, rows.map((placed, at) => commitRow(placed, pieces[at], columns, model, words))));
    element.style.setProperty("--columns", String(columns));
    element.style.setProperty("--column-width", `${Chain.COLUMN}px`);
    return element;
  }

  const KINDS = { desk, chain };

  function draw(model, words) {
    if (!(model.kind in KINDS)) throw new RangeError(`no picture of kind ${model.kind}`);
    return KINDS[model.kind](model, words);
  }

  return { draw };
})();
