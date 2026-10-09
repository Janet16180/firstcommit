"use strict";

/*
 * One command's card in the field guide: what it does in one sentence, its picture before and
 * after (or one picture when it only looks), what real git printed, the common beginner mistake,
 * where the game teaches it, and related commands. Every word arrives localized: the card's own
 * (GuideText.card) and the pictures' (for GuidePictures). Needs dom.js and guide-pictures.js;
 * guide.css styles it. Defines one global, GuideCard.
 *
 * create(card, words, {onRelated, onConflict}) {element}: card = {command, what, tag, picture,
 *   changed, same, sections, runs: [[{command, output}]], look, refused, mistake, where, related,
 *   conflict, playground}. `picture` is {before, after}, or {frames, between}: frames side by
 *   side, joined by an arrow, or by "or" when `between` is "or". A frame is {label, command,
 *   caption, show: [picture model], run: [{command, output}], look, refused, gloss, stop, decode,
 *   message}: `stop` makes it a refusal's frame; `decode` puts the run's lines beside its chain,
 *   row for row; `message` shows a commit message as an editor would. `changed` and `same` say in
 *   words what the command changed and what it left alone. `sections` are folded parts, closed
 *   at first ({title, frames, between, run, look, refused}), or with `fold: false` a titled part
 *   always shown. `look` and `refused` are pieces of git's output to mark: a line that matches
 *   the picture, or git's refusal (never gold, which means "changed"). `sum` ([{command, says}])
 *   shows a command as the two it does at once; `glyphs` ([[symbol, meaning]]) is a key of git's
 *   drawing. `picture` may be left out when sections hold the whole picture. Words may be text,
 *   or a list of text, {code} and {em} (a commit's subject, in italics).
 *   A related command's button calls onRelated(command); with `conflict`, a button calls
 *   onConflict(); with `playground` ({start, view, try}), a link opens that free-play start.
 * terminal(runs, silent, fold, marks) {element}: transcripts [[{command, output}]] as a night
 *   terminal, with marks {look, refused} on pieces of the output.
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

  /* One line of output, the pieces in `marks` wrapped in their mark: .gc-look or .gc-refused. */
  function marked(line, { look = [], refused = [] }) {
    const pieces = [...look.map((text) => [text, "gc-look"]), ...refused.map((text) => [text, "gc-refused"])].filter(([text]) => line.includes(text));
    if (pieces.length === 0) return [line];
    const [text, kind] = pieces.sort((a, b) => line.indexOf(a[0]) - line.indexOf(b[0]))[0];
    const at = line.indexOf(text);
    return [line.slice(0, at), el("span", { class: kind }, text), ...marked(line.slice(at + text.length), { look, refused })];
  }

  /* Transcripts as a terminal shows them: "$ command", then what it printed, or `silent` in
     the soft ink for a command that printed nothing. With `fold`, lines past the key ones of
     each output are .gc-more, hidden until the terminal is open. */
  function terminal(runs, silent, fold = false, marks = {}) {
    const lines = runs.flat().map(({ command, output }) => [
      el("span", { class: "gc-prompt" }, "$ "), el("span", { class: "gc-typed" }, command), "\n",
      output === "" ? el("span", { class: "gc-silent" }, `${silent}\n`) : output.replace(/\n$/, "").split("\n").map((line, at) => el("span", { class: fold && !isKey(line, at) ? "gc-more" : null }, marked(line, marks), "\n")),
    ]);
    return el("pre", { class: "gc-term" }, lines);
  }

  /* The card's terminal, folded to its key lines, with a Show all button when it hid any. */
  function printed(runs, words, marks = {}) {
    const pre = terminal(runs, words.card.silent, true, marks);
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

  /* Words as elements: text, or a list of text, {code} and {em}. */
  const said = (words) => (Array.isArray(words) ? words.map((piece) => (typeof piece === "string" ? piece : piece.code ? el("code", {}, piece.code) : el("em", {}, piece.em))) : words);

  /* git's graph beside its chain: the command, then one line of output per row of the picture. */
  function decoder(frame, words) {
    const [{ command, output }] = frame.run;
    const lines = output.replace(/\n$/, "").split("\n");
    const term = el("pre", { class: "gc-term" },
      el("span", { class: "gc-line" }, el("span", { class: "gc-prompt" }, "$ "), el("span", { class: "gc-typed" }, command)),
      lines.map((line) => el("span", { class: "gc-line" }, line || " ")));
    return el("div", { class: "gc-decoder" }, term, el("div", { class: "gc-decoded" }, frame.show.map((model) => GuidePictures.draw(model, words.pictures, { lines }))));
  }

  /* A commit message as the editor shows it: its subject marked, git's comment lines in soft ink. */
  function editor(message) {
    const [subject, ...rest] = message.replace(/\n$/, "").split("\n");
    return el("pre", { class: "gc-editor" },
      el("span", { class: "gc-editor-bar" }, ".git/MERGE_MSG"),
      el("span", { class: "gc-look" }, subject), "\n",
      rest.map((line) => [el("span", { class: line.startsWith("#") ? "gc-comment" : null }, line), "\n"]));
  }

  /* A frame's label: its words, then the command it runs. */
  function labelOf({ label, command }) {
    if (!label && !command) return null;
    return el("span", { class: "gc-label" }, said(label), label && command ? " " : null, command ? el("code", {}, command) : null);
  }

  function frameOf(frame, words) {
    const label = labelOf(frame);
    const body = frame.decode ? [decoder(frame, words)] : [
      (frame.show || []).map((model) => GuidePictures.draw(model, words.pictures)),
      frame.message ? editor(frame.message) : null,
      frame.run ? terminal([frame.run], words.card.silent, false, frame) : null,
    ];
    return el("figure", { class: frame.stop ? "gc-frame is-refused" : "gc-frame" },
      el("figcaption", {}, label, frame.caption ? [" ", said(frame.caption)] : null),
      body,
      frame.gloss ? el("p", { class: "gc-gloss" }, said(frame.gloss)) : null);
  }

  /* Frames side by side, joined by an arrow, or by "or" for outcomes. */
  function frames(list, between, words) {
    const join = () => (between === "or" ? el("span", { class: "gc-or" }, words.card.or) : el("span", { class: "gc-then", "aria-hidden": "true" }));
    return el("div", { class: list.length > 2 ? "gc-frames is-steps" : "gc-frames" }, list.flatMap((frame, at) => [at > 0 ? join() : null, frameOf(frame, words)]));
  }

  function facts(card, words) {
    if (!card.changed && !card.same) return null;
    const fact = (kind, text) => (text ? el("li", { class: `gc-fact is-${kind}` }, el("span", { class: "gc-fact-kind" }, words.card[kind]), " ", said(text)) : null);
    return el("ul", { class: "gc-facts", role: "list" }, fact("changed", card.changed), fact("same", card.same));
  }

  function section(item, words) {
    const body = [frames(item.frames, item.between, words), item.run ? terminal([item.run], words.card.silent, false, item) : null];
    if (item.fold === false) return el("section", { class: "gc-section" }, el("h3", {}, said(item.title)), body);
    return el("details", { class: "gc-section" }, el("summary", {}, said(item.title)), body);
  }

  function sum(parts) {
    const box = ({ command, says }) => el("span", { class: "gc-sum-part" }, el("code", {}, command), el("small", {}, said(says)));
    return el("p", { class: "gc-sum" }, parts.flatMap((item, at) => [at === 0 ? null : el("span", { class: "gc-sum-op", "aria-hidden": "true" }, at === parts.length - 1 ? "=" : "+"), box(item)]));
  }

  const glyphs = (pairs) => el("dl", { class: "gc-glyphs" }, pairs.map(([symbol, meaning]) => [el("dt", {}, el("code", {}, symbol)), el("dd", {}, said(meaning))]));

  /* Every picture model on the card, in its frames and its sections. */
  function models(card) {
    const framed = (list) => list.flatMap((frame) => frame.show || []);
    const own = !card.picture ? [] : card.picture.frames ? framed(card.picture.frames) : [card.picture.before];
    return [...own, ...(card.sections || []).flatMap((item) => framed(item.frames))];
  }

  function picture(card, words) {
    if (!card.picture) return null;
    return card.picture.frames ? frames(card.picture.frames, card.picture.between, words) : pictures(card.picture, words);
  }

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
      card.sum ? sum(card.sum) : null,
      picture(card, words),
      facts(card, words),
      card.glyphs ? glyphs(card.glyphs) : null,
      models(card).some((model) => model.kind === "chain") ? el("p", { class: "gc-key" }, words.card.chainKey) : null,
      (card.sections || []).map((item) => section(item, words)),
      card.runs.length > 0 ? part(words.card.prints, printed(card.runs, words, card)) : null,
      part(words.card.mistake, el("p", {}, said(card.mistake))),
      part(words.card.related, el("ul", { class: "gc-related", role: "list" },
        card.related.map((command) => el("li", {}, el("button", { type: "button", class: "btn", onclick: () => onRelated(command) }, command))))));
  }

  return { create, terminal, playgroundHref };
})();
