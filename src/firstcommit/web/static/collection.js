"use strict";

/*
 * The command collection: one card per mission, in play order. A finished mission's card shows
 * its command and what it does (Status.collection); the others stay locked until finished. It
 * opens on the browser's own <dialog> (focus stays inside, Escape closes it). Needs dom.js,
 * markup.js and progress.js. Defines one global, Collection.
 */

/* global Dom, Markup, Progress */
/* exported Collection */

const Collection = (function () {
  const { el } = Dom;

  /* A card, coloured by its sector's place on the map (0-based); `card` is null while locked. */
  function cardElement(card, sector, number) {
    if (!card) return el("div", { class: "cmdcard is-locked", "data-sector": String(sector) }, el("code", {}, "???"), el("p", {}, `Finish mission ${number} to unlock it.`));
    return el("div", { class: "cmdcard", "data-sector": String(sector) }, el("code", {}, card.command), Markup.render(card.text));
  }

  /* Opens the collection for `status` (Status) and returns its dialog. */
  function open(status) {
    const cards = new Map(status.collection.map((card) => [card.level, card]));
    const grid = status.chapters.flatMap((chapter, sector) => chapter.levels.map((level) => cardElement(cards.get(level.id) || null, sector, Progress.missionNumber(status.chapters, level.id).number)));
    const dialog = el("dialog", { class: "collection px", "aria-labelledby": "collection-title" },
      el("h2", { id: "collection-title" }, "Command collection"),
      el("p", {}, "Every mission you finish gives you a card. Look here when you forget a command."),
      el("div", { class: "coll-grid" }, grid),
      el("button", { type: "button", class: "btn close", onclick: () => dialog.close() }, "Close"),
    );
    dialog.addEventListener("close", () => dialog.remove());
    document.body.append(dialog);
    dialog.showModal();
    return dialog;
  }

  return { open, card: cardElement };
})();
