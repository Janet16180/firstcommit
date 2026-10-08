"use strict";

/*
 * One command's card in the field guide: what it does in one sentence, its picture before and
 * after (or one picture when it only looks), what real git printed, the common beginner mistake,
 * where the game teaches it, and related commands. Every word arrives localized: the card's own
 * (GuideText.card) and the pictures' (for GuidePictures). Needs dom.js and guide-pictures.js;
 * guide.css styles it. Defines one global, GuideCard.
 *
 * create(card, words, {onRelated, onConflict}) {element}: card = {command, what, tag, picture:
 *   {before, after}, runs: [[{command, output}]], mistake, where, related, conflict}. A related
 *   command's button calls onRelated(command); with `conflict`, a button calls onConflict().
 * terminal(runs, silent) {element}: transcripts [[{command, output}]] as a night terminal.
 */

/* global Dom, GuidePictures */
/* exported GuideCard */

const GuideCard = (function () {
  const { el } = Dom;
  let made = 0;

  function figure(caption, model, words) {
    return el("figure", { class: "gc-figure" }, el("figcaption", {}, caption), GuidePictures.draw(model, words.pictures));
  }

  function pictures({ before, after }, words) {
    if (!after) return el("div", { class: "gc-pictures" }, figure(words.card.onlyLooks, before, words));
    return el("div", { class: "gc-pictures" },
      figure(words.card.before, before, words),
      el("span", { class: "gc-then", "aria-hidden": "true" }),
      figure(words.card.after, after, words));
  }

  /* Transcripts as a terminal shows them: "$ command", then what it printed, or `silent` in
     the soft ink for a command that printed nothing. */
  function terminal(runs, silent) {
    const lines = runs.flat().map(({ command, output }) => [
      el("span", { class: "gc-prompt" }, "$ "), el("span", { class: "gc-typed" }, command), "\n",
      output === "" ? el("span", { class: "gc-silent" }, `${silent}\n`) : output,
    ]);
    return el("pre", { class: "gc-term" }, lines);
  }

  const part = (title, ...body) => el("section", { class: "gc-part" }, el("h3", {}, title), body);

  function create(card, words, { onRelated, onConflict }) {
    made += 1;
    const id = `guide-card-${made}`;
    return el("article", { class: "guide-card", "aria-labelledby": id },
      el("header", { class: "gc-head" },
        el("h2", { class: "gc-command", id }, el("code", {}, card.command)),
        card.tag === null ? null : el("span", { class: "gc-tag" }, card.tag)),
      el("p", { class: "gc-meaning" }, card.what),
      pictures(card.picture, words),
      part(words.card.prints, terminal(card.runs, words.card.silent)),
      part(words.card.mistake, el("p", {}, card.mistake)),
      part(words.card.taught, el("p", {}, card.where)),
      part(words.card.related, el("ul", { class: "gc-related", role: "list" },
        card.related.map((command) => el("li", {}, el("button", { type: "button", class: "btn", onclick: () => onRelated(command) }, command))))),
      card.conflict ? el("button", { type: "button", class: "btn gc-conflict", onclick: onConflict }, words.card.conflict) : null);
  }

  return { create, terminal };
})();
