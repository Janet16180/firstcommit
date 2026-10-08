"use strict";

/*
 * The field guide cards' small pictures, in the look of the game's teaching pictures
 * (docs/drafts/teaching-pictures.md): the desk (Git's places with the files in them) and the
 * chain (commits newest first, each joined to its parents, with name tags and HEAD). The chain
 * copies chain.js's look (p2/orbit-frontend: its column step, square capsules, wires, tags, HEAD
 * mark and pins), not its code, since chain.js is not on this branch yet; once it is, this
 * module should draw with it, so the game keeps one chain renderer.
 * Every word comes from `words` (GuideText.pictures localized, plus `places`, each place's
 * label); a file's state is written beside it and each commit row says whose it is to a screen
 * reader, so colour is never the only clue. Needs dom.js; guide.css styles it. Defines one
 * global, GuidePictures.
 *
 * draw(model, words) {element}: model is a desk or a chain as GuideText describes them;
 *   another kind throws a RangeError.
 */

/* global Dom */
/* exported GuidePictures */

const GuidePictures = (function () {
  const { el, svg } = Dom;
  const PLACES = ["folder", "staging", "vault", "remote"];
  /* The lane's geometry in px, one row per commit: the first column's centre, the step between
     columns, a row's height (guide.css's --gp-row) and a capsule's size. */
  const X0 = 10;
  const COLUMN = 22;
  const ROW = 36;
  const CAPSULE = { width: 16, height: 16 };

  const fresh = (item, base) => (item.fresh ? `${base} gp-fresh` : base);

  function chip(item, words) {
    const state = item.state ? el("span", { class: "gp-state" }, words.states[item.state]) : null;
    return el("li", { class: fresh(item, `gp-chip gp-chip--${item.state || "plain"}`) }, el("span", { class: "gp-file" }, item.name), state);
  }

  function place(key, items, words) {
    const absent = items === null;
    const body = absent
      ? el("p", { class: "gp-none" }, words.notYet)
      : items.length === 0
        ? el("p", { class: "gp-none" }, words.empty)
        : el("ul", { class: "gp-chips", role: "list" }, items.map((item) => chip(item, words)));
    return el("section", { class: `gp-place gp-place--${key}${absent ? " gp-place--absent" : ""}` },
      el("h4", { class: "gp-place-name" }, words.places[key]),
      body);
  }

  function desk(model, words) {
    return el("div", { class: "gp gp-desk" }, PLACES.filter((key) => key in model).map((key) => place(key, model[key], words)));
  }

  const centre = (row, col) => ({ x: X0 + col * COLUMN, y: ROW / 2 + row * ROW });

  function lane(commits) {
    const rowOf = new Map(commits.map((commit, row) => [commit.id, row]));
    const columns = Math.max(...commits.map((commit) => commit.col)) + 1;
    const width = 2 * X0 + (columns - 1) * COLUMN;
    const height = commits.length * ROW;
    /* Down its own column, turning into the parent's in the parent's last half row, as git
       --graph draws a side line joining back. */
    const links = commits.flatMap((commit, row) => commit.parents.map((parent) => {
      const from = centre(row, commit.col);
      const to = centre(rowOf.get(parent), commits[rowOf.get(parent)].col);
      const look = commit.ghost ? "ghost" : commit.who === "mothership" ? "mothership" : "line";
      return svg("path", { class: `gp-link gp-link--${look}`, d: `M${from.x} ${from.y} L${from.x} ${to.y - ROW / 2} L${to.x} ${to.y}` });
    }));
    const capsules = commits.map((commit, row) => {
      const { x, y } = centre(row, commit.col);
      const look = commit.ghost ? "ghost" : commit.who || "you";
      return svg("rect", { class: fresh(commit, `gp-capsule gp-capsule--${look}`), x: x - CAPSULE.width / 2, y: y - CAPSULE.height / 2, width: CAPSULE.width, height: CAPSULE.height });
    });
    return svg("svg", { class: "gp-lane", viewBox: `0 0 ${width} ${height}`, width, height, "aria-hidden": "true" }, links, capsules);
  }

  function tag(name, head) {
    const kind = head ? "head" : name.kind;
    return el("span", { class: fresh(name, `gp-tag gp-tag--${kind}`) }, name.name);
  }

  const headMark = (words) => el("span", { class: "gp-head", title: words.head }, "HEAD");

  function commitRow(commit, model, words) {
    const who = commit.ghost ? words.ghost : commit.who === "mothership" ? words.notYours : words.by[commit.who || "you"];
    const names = model.names.filter((name) => name.on === commit.id);
    return el("li", { class: "gp-row" },
      el("span", { class: "gp-sr" }, who),
      model.head === commit.id ? headMark(words) : null,
      names.map((name) => (name.name === model.head ? el("span", { class: "gp-rides" }, headMark(words), tag(name, true)) : tag(name, false))));
  }

  function chain(model, words) {
    return el("div", { class: "gp gp-chain" },
      lane(model.commits),
      el("ol", { class: "gp-rows", role: "list" }, model.commits.map((commit) => commitRow(commit, model, words))));
  }

  const KINDS = { desk, chain };

  function draw(model, words) {
    if (!(model.kind in KINDS)) throw new RangeError(`no picture of kind ${model.kind}`);
    return KINDS[model.kind](model, words);
  }

  return { draw };
})();
