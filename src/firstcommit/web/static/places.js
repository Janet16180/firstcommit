"use strict";

/*
 * How the page names Git's four places: the real git name first, the game's name after it in
 * brackets ("Working folder (workshop)"). The game's name is its own span, so a tight spot (a
 * phone, a small card) can drop it and keep the real name. Needs dom.js and strings.js. Defines
 * one global, Places.
 *
 * IDS                the places, by the zones' ids.
 * label(id)          the name as an element: the real name, then span.place-game.
 * text(id)           the same name as plain text, for an aria-label or a sentence.
 */

/* global Dom, Strings */
/* exported Places */

const Places = (function () {
  const { el } = Dom;
  const { t } = Strings;
  const IDS = ["workshop", "dock", "vault", "remote"];

  const label = (id) => el("span", { class: "place" }, t(`place.${id}`), el("span", { class: "place-game" }, ` (${t(`place.${id}.game`)})`));
  const text = (id) => `${t(`place.${id}`)} (${t(`place.${id}.game`)})`;

  return { IDS, label, text };
})();
