"use strict";

/*
 * One command's card in the field guide: what it does in one sentence, its picture before and
 * after (or one picture when it only looks), what real git printed, the common beginner mistake,
 * where the game teaches it, and related commands. Every word arrives localized: the card's own
 * (GuideText.card) and the pictures' (for GuidePictures). Needs dom.js and guide-pictures.js;
 * guide.css styles it. Defines one global, GuideCard.
 *
 * create(card, words, {onRelated, onConflict}) {element}: card = {command, what, tag, picture:
 *   {before, after}, runs: [[{command, output}]], mistake, where, related, conflict, playground}.
 *   A related command's button calls onRelated(command); with `conflict`, a button calls
 *   onConflict(); with `playground` ({start, view, try}), a link opens that free-play start.
 * terminal(runs, silent) {element}: transcripts [[{command, output}]] as a night terminal.
 * playgroundHref({start, view, try}) the playground's address for that start, view and command.
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

  /* How many lines of one command's output a folded terminal shows; git's hints never. */
  const KEY_LINES = 8;
  const isKey = (line, at) => at < KEY_LINES && !line.startsWith("hint: ");

  /* Transcripts as a terminal shows them: "$ command", then what it printed, or `silent` in
     the soft ink for a command that printed nothing. With `fold`, lines past the key ones of
     each output are .gc-more, hidden until the terminal is open. */
  function terminal(runs, silent, fold = false) {
    const lines = runs.flat().map(({ command, output }) => [
      el("span", { class: "gc-prompt" }, "$ "), el("span", { class: "gc-typed" }, command), "\n",
      output === "" ? el("span", { class: "gc-silent" }, `${silent}\n`) : output.replace(/\n$/, "").split("\n").map((line, at) => el("span", { class: fold && !isKey(line, at) ? "gc-more" : null }, `${line}\n`)),
    ]);
    return el("pre", { class: "gc-term" }, lines);
  }

  /* The card's terminal, folded to its key lines, with a Show all button when it hid any. */
  function printed(runs, words) {
    const pre = terminal(runs, words.card.silent, true);
    const hidden = pre.querySelectorAll(".gc-more").length;
    if (hidden === 0) return pre;
    const total = pre.textContent.replace(/\n$/, "").split("\n").length;
    const more = words.card.showAll.replace("{count}", String(total));
    const button = el("button", {
      type: "button", class: "btn gc-show", "aria-expanded": "false",
      onclick: () => {
        const open = pre.classList.toggle("is-open");
        button.setAttribute("aria-expanded", String(open));
        button.textContent = open ? words.card.showLess : more;
      },
    }, more);
    return [pre, button];
  }

  /* The free playground's address for a start ({start, view, try}): each value URI-encoded,
     so a command's spaces, quotes, "&" and "=" come back as typed. */
  function playgroundHref(link) {
    const fields = ["start", "view", "try"].filter((key) => link[key] !== undefined);
    return `#/playground?${fields.map((key) => `${key}=${encodeURIComponent(link[key])}`).join("&")}`;
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
      el("p", { class: "gc-where" }, el("strong", {}, `${words.card.taught}: `), card.where),
      card.playground || card.conflict ? el("div", { class: "gc-actions" },
        card.playground ? el("a", { class: "btn gc-try", href: playgroundHref(card.playground) }, words.card.tryIt) : null,
        card.conflict ? el("button", { type: "button", class: "btn gc-conflict", onclick: onConflict }, words.card.conflict) : null) : null,
      pictures(card.picture, words),
      card.picture.before.kind === "chain" ? el("p", { class: "gc-key" }, words.card.chainKey) : null,
      part(words.card.prints, printed(card.runs, words)),
      part(words.card.mistake, el("p", {}, card.mistake)),
      part(words.card.related, el("ul", { class: "gc-related", role: "list" },
        card.related.map((command) => el("li", {}, el("button", { type: "button", class: "btn", onclick: () => onRelated(command) }, command))))));
  }

  return { create, terminal, playgroundHref };
})();
