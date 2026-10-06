"use strict";

/*
 * Showing the game's text. The server parses every text (firstcommit/markup.py) into blocks:
 * {kind: "para", spans}, {kind: "code", text} and {kind: "bullets", items: [spans]}, where a
 * span is {text, code}. This only turns blocks into elements; it never parses text itself
 * (Ring Zero audit JS-8). Needs dom.js. Defines one global, Markup.
 */

/* global Dom */
/* exported Markup */

const Markup = (() => {
  const { el } = Dom;

  /* Code of several words is split into words that never break inside (the stylesheet keeps
     each word whole), so a line may break only at a space: `--global` never splits at a hyphen. */
  function codeSpan(text) {
    const words = text.split(" ");
    if (words.length === 1) return el("code", {}, text);
    return el("code", { class: "words" }, words.flatMap((word, index) => (index ? [" ", el("span", {}, word)] : [el("span", {}, word)])));
  }

  const spans = (list) => list.map((span) => (span.code ? codeSpan(span.text) : span.text));

  const BLOCKS = {
    para: (block) => el("p", {}, spans(block.spans)),
    code: (block) => el("pre", { class: "code" }, el("code", {}, block.text)),
    bullets: (block) => el("ul", {}, block.items.map((item) => el("li", {}, spans(item)))),
  };

  function blockElement(block) {
    const make = BLOCKS[block.kind];
    if (!make) throw new Error(`unknown block kind: ${block.kind}`);
    return make(block);
  }

  /* The blocks as elements, in order. */
  const render = (blocks) => blocks.map(blockElement);

  const spanText = (list) => list.map((span) => span.text).join("");
  const PLAIN = {
    para: (block) => spanText(block.spans),
    code: (block) => block.text,
    bullets: (block) => block.items.map(spanText).join("\n"),
  };

  /* The blocks as plain text, one line per paragraph or item: for titles and labels. */
  const plain = (blocks) => blocks.map((block) => PLAIN[block.kind](block)).join("\n");

  return { render, spans, plain };
})();
