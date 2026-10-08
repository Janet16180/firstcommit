"use strict";

/*
 * Click to keep (docs/drafts/playground/plan.md, "Merge conflicts, two ways"): the field guide's
 * Markers decoded on the playground's real file. Each file with conflict markers is shown as the
 * server parsed it: the lines Git merged on its own, untagged, and each block's two sides, the
 * repository's own side at HEAD (you violet, Alex green) and the other below the fence; the
 * marker's long hash is shortened. Picking a side only marks lines; Write sends the picks with the
 * name of the text they were made on, and the server rewrites the marker blocks. A refused Write
 * (409: the file changed) writes nothing, clears the picks and makes Look again the main button.
 * A new read of the file drops picks made on the old text, and so does an editor opening it:
 * while it is open the panel greys and waits. Once the markers are gone (a file still unmerged
 * with no block left, or one git add has taken) it shows the file as it is now and what to type next; the page never runs git. Under it, two chips type `nano <file>`
 * or `vim <file>` at the prompt. Needs dom.js and strings.js. Defines one global, KeepPanel.
 *
 * create({onWrite, onType}) {element, update({person, marked, texts, editing})}: onWrite({file,
 *   read, choices}) writes the picks (a promise; a 409 rejection is the file having changed);
 *   onType(line) types at the prompt. person is whose repository ("you" or "alex"), marked and
 *   texts that person's (PlaygroundObservation), editing {editor, path} while an editor runs in
 *   that person's terminal, else null.
 */

/* global Dom, Strings */
/* exported KeepPanel */

const KeepPanel = (function () {
  const { el } = Dom;
  const { t, parts } = Strings;
  const CHOICES = ["yours", "theirs", "both"];
  const EDITORS = ["nano", "vim"];
  const LONG_HASH = /^[0-9a-f]{40}$/;

  const other = (person) => (person === "alex" ? "you" : "alex");
  const short = (label) => (LONG_HASH.test(label) ? `${label.slice(0, 7)}…` : label);
  const said = (key, params) => parts(key, params).map((part) => (typeof part === "string" ? part : el("code", {}, part.code)));
  const textLines = (text) => text.replace(/\n$/, "").split("\n");

  function line(text, part, { title = null, classes = [], tag = null } = {}) {
    return el("li", { class: ["keep-line", ...classes].join(" "), "data-part": part },
      el("span", { class: "keep-text", title }, text),
      tag && el("span", { class: "keep-tag", "data-who": tag }, t(`pg.who.${tag}`)));
  }

  /* One conflict block's lines, as the pick for it leaves them, and the row of its picks. */
  function block(part, choice, { person, locked, pick }) {
    const marker = (text, name, full = text) => line(text, name, { title: full, classes: ["is-marker", choice && "is-gone"].filter(Boolean) });
    const side = (lines, name, who, dropped) => lines.map((text) => line(text, name, { tag: who, classes: dropped ? ["is-dropped"] : [] }));
    const owner = { yours: person, theirs: other(person) };
    const button = (value) => el("button", {
      type: "button", class: "keep-pick", "data-choice": value, "data-who": owner[value] || "both", "aria-pressed": String(choice === value), disabled: locked, onclick: () => pick(value),
    }, value === "both" ? t("pg.keep.both") : t(`pg.keep.side.${owner[value]}`));
    return [
      marker(`<<<<<<< ${part.yours_label}`, "ours-start"),
      ...side(part.yours, "ours", person, choice === "theirs"),
      marker("=======", "fence"),
      ...side(part.theirs, "theirs", other(person), choice === "yours"),
      marker(`>>>>>>> ${short(part.theirs_label)}`, "theirs-end", `>>>>>>> ${part.theirs_label}`),
      el("li", { class: "keep-choose" }, el("span", {}, t("pg.keep.keep")), CHOICES.map(button)),
    ];
  }

  function chips(file, { editing, onType }) {
    return el("div", { class: "keep-or" }, el("p", {}, t("pg.keep.or")), EDITORS.map((editor) => el("button", {
      type: "button", class: "keep-chip", "data-editor": editor, disabled: Boolean(editing), onclick: () => onType(`${editor} ${file}`),
    }, `${editor} ${file}`)));
  }

  function create({ onWrite, onType }) {
    const element = el("section", { class: "keep", "aria-label": t("pg.view.conflict") });
    const state = { reads: new Map(), picks: new Map(), stale: new Set(), written: new Set(), seen: [], last: null };

    function marked(file, { person, editing }) {
      const picks = state.picks.get(file.path) || [];
      const stale = state.stale.has(file.path);
      const blocks = file.parts.filter((part) => part.kind === "block");
      const ready = blocks.length > 0 && blocks.every((part, at) => picks[at]) && !editing && !stale;
      const pick = (at) => (value) => {
        state.picks.set(file.path, Object.assign([...picks], { [at]: value }));
        draw();
      };
      let at = -1;
      const items = file.parts.flatMap((part) => {
        if (part.kind === "clean") return part.lines.map((text) => line(text, "same"));
        at += 1;
        return block(part, picks[at], { person, locked: Boolean(editing) || stale, pick: pick(at) });
      });
      const write = el("button", { type: "button", class: "btn keep-write", disabled: !ready, onclick: () => send(file, picks) }, t("pg.keep.write", { file: file.path }));
      const look = stale ? el("button", { type: "button", class: "btn btn-primary keep-look", onclick: () => lookAgain(file.path) }, t("pg.keep.look")) : null;
      let message = null;
      if (editing) message = el("p", { class: "keep-message is-waiting" }, t("pg.keep.wait", { file: file.path, editor: editing.editor }));
      else if (stale) message = el("p", { class: "keep-message is-error" }, t("pg.keep.stale", { file: file.path }));
      return el("div", { class: "keep-file" },
        el("p", { class: "keep-outside" }, t("pg.keep.outside")),
        el("div", { class: "keep-box" },
          el("h3", { class: "keep-head" }, el("span", {}, file.path), el("span", { class: "keep-state" }, t("pg.keep.blocks", { count: blocks.length }))),
          el("ol", { class: "keep-lines" }, items)),
        el("div", { class: "keep-act" }, look, write),
        message,
        chips(file.path, { editing, onType }));
    }

    /* A file with no markers left, as it is now: its lines, and what to type next. */
    function resolved(path, lines) {
      const written = state.written.has(path) ? `${t("pg.keep.written")} ` : "";
      return el("div", { class: "keep-file" },
        el("div", { class: "keep-box" },
          el("h3", { class: "keep-head" }, el("span", {}, t("pg.keep.now", { file: path })), el("span", { class: "keep-state is-ok" }, t("pg.keep.clean"))),
          el("ol", { class: "keep-lines" }, lines.map((entry) => line(entry, "same")))),
        el("p", { class: "keep-message is-ok" }, written, said("pg.keep.next", { file: path })));
    }

    function draw() {
      const { person, marked: files, texts, editing } = state.last;
      element.dataset.person = person;
      element.classList.toggle("is-waiting", Boolean(editing));
      const blocked = (file) => file.parts.some((part) => part.kind === "block");
      const listed = files.map((file) => file.path);
      const folder = (path) => (texts.find((entry) => entry.path === path) || {}).folder;
      const shown = [
        ...files.map((file) => (blocked(file) ? marked(file, { person, editing }) : resolved(file.path, file.parts.flatMap((part) => part.lines)))),
        ...state.seen.filter((path) => !listed.includes(path) && typeof folder(path) === "string").map((path) => resolved(path, textLines(folder(path)))),
      ];
      element.replaceChildren(...(shown.length ? shown : [el("p", { class: "keep-none" }, t("pg.keep.none"))]));
    }

    function send(file, picks) {
      return onWrite({ file: file.path, read: file.read, choices: [...picks] }).then(() => {
        state.written.add(file.path);
      }, (error) => {
        if (error.status !== 409) throw error;
        state.stale.add(file.path);
        state.picks.delete(file.path);
        draw();
      });
    }

    function lookAgain(path) {
      state.stale.delete(path);
      draw();
    }

    function update({ person, marked: files, texts, editing }) {
      for (const file of files) {
        if (state.reads.get(file.path) !== file.read || editing) state.picks.delete(file.path);
        state.reads.set(file.path, file.read);
        if (!state.seen.includes(file.path)) state.seen.push(file.path);
      }
      for (const path of state.stale) if (!files.some((file) => file.path === path)) state.stale.delete(path);
      state.last = { person, marked: files, texts, editing };
      draw();
    }

    return { element, update };
  }

  return { create };
})();
