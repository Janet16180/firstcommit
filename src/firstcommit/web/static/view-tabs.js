"use strict";

/*
 * The row of views over the level screen's stage (docs/drafts/chapters-5-9.md, the view ladder):
 * one tab per view the player has seen, so the older view is always one tap away. It is born
 * with two tabs and gains one per new view; with fewer than two it stays hidden. It only shows
 * the row and says which tab was picked; which view a level opens on, and which views were seen,
 * are the game's to say. Needs dom.js and strings.js. Defines one global, ViewTabs.
 *
 * ORDER                 the views in the ladder's order, as the game names them.
 * tabs(seen, crew)      the tabs for the views `seen`, in that order; in a level with a teammate
 *                       (`crew`) the crew view stands in for your station, else the other way.
 * create({tabs, current, onPick})
 *                       {element, select(view)}: the row with `current` chosen; a click or an
 *                       arrow key chooses another tab and calls onPick(view).
 */

/* global Dom, Strings */
/* exported ViewTabs */

const ViewTabs = (function () {
  const { el } = Dom;
  const { t } = Strings;
  const ORDER = Object.freeze(["station", "crew", "history", "sides", "blackbox", "board", "focus"]);

  function tabs(seen, crew) {
    const absent = crew ? "station" : "crew";
    return ORDER.filter((view) => seen.includes(view) && view !== absent);
  }

  function create({ tabs: views, current, onPick }) {
    const buttons = views.map((view) => el("button", { type: "button", role: "tab", class: "view-tab", "data-view": view, onclick: () => pick(view) }, t(`views.tab.${view}`)));
    const element = el("nav", { class: "view-tabs", role: "tablist", "aria-label": t("views.label"), hidden: views.length < 2 }, buttons);
    let chosen = current;

    function select(view) {
      chosen = view;
      for (const button of buttons) {
        const on = button.dataset.view === view;
        button.setAttribute("aria-selected", String(on));
        button.tabIndex = on ? 0 : -1;
      }
    }

    function pick(view) {
      select(view);
      onPick(view);
    }

    element.addEventListener("keydown", (event) => {
      const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
      if (!step) return;
      const next = views[(views.indexOf(chosen) + step + views.length) % views.length];
      pick(next);
      buttons[views.indexOf(next)].focus();
    });
    select(current);
    return { element, select };
  }

  return { ORDER, tabs, create };
})();
