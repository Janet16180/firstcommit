"use strict";

/*
 * The map screen: Rama and the game's name, a bar with the stars won, the missions done, the
 * field guide, the cards due and the look and sound buttons, then every chapter as a
 * sector in play order. A sector with missions is a strip of space with its planet and its
 * numbered mission nodes along a route; a chapter with none yet is a sector coming soon.
 * Choosing a node shows its mission on the card at the bottom (its command and best stars),
 * whose button opens the level. Everything comes from firstcommit/game.py's Status. Needs
 * dom.js, art-sprites.js, art-sky.js, progress.js and dialog.js. Defines one
 * global, StarMap.
 */

/* global Dom, ArtSprites, ArtSky, Progress, Dialog */
/* exported StarMap */

const StarMap = (function () {
  const { el, svg } = Dom;
  const levelHref = (id) => `#/level/${encodeURIComponent(id)}`;
  const plural = (count, word) => `${count} ${word}${count === 1 ? "" : "s"}`;

  /* Where the nodes of a sector with `count` missions sit on its route, in percent of the route's box. */
  const routePoints = (count) => Array.from({ length: count }, (_, index) => [count === 1 ? 50 : (index / (count - 1)) * 100, index % 2 ? 68 : 42]);

  /* The mission Rama points at: the one in progress, else the next one not done. */
  function hereId(status) {
    const active = status.active && Progress.findLevel(status.chapters, status.active.level);
    const next = Progress.nextLevel(status.chapters);
    return active ? active.id : next ? next.id : null;
  }

  function head() {
    return el("header", { class: "map-top" },
      ArtSprites.rama({ size: "header" }),
      el("div", {},
        el("h1", { class: "map-title" }, "First Commit"),
        el("p", { class: "map-lede" }, "Learn Git one mission at a time. Each mission teaches you a command, and you try it with real git in a real terminal."),
      ),
    );
  }

  function bar(status, prefButtons) {
    const levels = status.chapters.flatMap((chapter) => chapter.levels);
    const done = levels.filter((level) => level.done).length;
    const stars = levels.reduce((sum, level) => sum + level.stars, 0);
    return el("div", { class: "map-bar" },
      el("span", { class: "counter px stars-won", role: "img", "aria-label": `${stars} of ${levels.length * 3} stars` }, ArtSprites.star(true), " ", el("b", {}, `${stars}/${levels.length * 3}`)),
      el("span", { class: "counter px" }, "Missions ", el("b", {}, `${done}/${levels.length}`)),
      el("span", { class: "spacer" }),
      el("a", { class: "btn field-guide-open", href: "#/guide" }, "Field guide"),
      status.cards_due > 0 && el("a", { class: "btn", href: "#/cards" }, `Review ${plural(status.cards_due, "card")}`),
      prefButtons(),
    );
  }

  function sectorHead(chapter, index) {
    const id = encodeURIComponent(chapter.id);
    return el("header", { class: "sector-head" },
      el("span", { class: "snum" }, `Sector ${index + 1}`),
      el("h2", {}, chapter.title),
      el("p", { class: "sector-blurb" }, chapter.blurb),
      chapter.levels.length > 0 && chapter.cards > 0 && el("p", { class: "sector-links" }, el("a", { href: `#/notes/${id}` }, "Notes"), el("a", { href: `#/cards/${id}` }, `Practise ${plural(chapter.cards, "card")}`)),
    );
  }

  function node(level, point, { number, here, onChoose }) {
    const label = `Mission ${number}: ${level.title}${level.done ? ", done" : ""}`;
    return el("button", {
      type: "button",
      class: level.done ? "node is-done" : "node",
      style: `left:${point[0]}%;top:${point[1]}%`,
      "data-level": level.id,
      "aria-label": label,
      onclick: () => onChoose(level.id),
    }, number, here && ArtSprites.rama({ size: "here" }));
  }

  function field(chapter, index, options) {
    const points = routePoints(chapter.levels.length);
    const line = svg("svg", { viewBox: "0 0 100 100", preserveAspectRatio: "none", "aria-hidden": "true" },
      svg("polyline", { "vector-effect": "non-scaling-stroke", points: points.map((point) => point.join(",")).join(" ") }));
    return el("div", { class: "field" },
      ArtSky.field(chapter.id),
      ArtSprites.planet(index),
      el("div", { class: "route" }, line, chapter.levels.map((level, place) => node(level, points[place], {
        number: `${index + 1}.${place + 1}`,
        here: level.id === options.here,
        onChoose: options.onChoose,
      }))),
    );
  }

  function sector(chapter, index, options) {
    if (!chapter.levels.length) {
      return el("section", { class: "sector is-soon" }, sectorHead(chapter, index), el("div", { class: "soon-field" }, "Coming soon"));
    }
    return el("section", { class: "sector" }, sectorHead(chapter, index), field(chapter, index, options));
  }

  function playLabel(level, active) {
    let label = "Start the mission";
    if (active && active.level === level.id) label = "Continue the mission";
    else if (level.done) label = "Play again";
    return label;
  }

  /* The card's contents for the chosen mission. */
  function cardParts(status, id) {
    const level = Progress.findLevel(status.chapters, id);
    const { sector: number, number: mission } = Progress.missionNumber(status.chapters, id);
    const { active } = status;
    const other = active && active.level !== id ? Progress.findLevel(status.chapters, active.level) : null;
    return [
      el("span", { class: "card-num" }, `Sector ${number}, mission ${mission}`),
      el("h2", { class: "card-title" }, level.title),
      el("div", { class: "card-meta" }, el("code", {}, level.command), ArtSprites.stars(level.stars)),
      el("p", { class: "card-note" }, other ? `Starting it ends “${other.title}”, which is in progress.` : ""),
      el("a", { class: "btn btn-primary", href: levelHref(id) }, playLabel(level, active)),
    ];
  }

  async function erase(ctx) {
    const sure = await Dialog.confirm({
      title: "Erase all progress?",
      text: "Your finished missions and card schedule are deleted, and any mission in progress ends. This cannot be undone.",
      confirm: "Erase everything",
      cancel: "Keep my progress",
      danger: true,
    });
    if (!sure) return;
    await ctx.game.reset();
    await ctx.refresh();
    ctx.reload();
  }

  /* ctx: status(), game, refresh(), reload() (shows this view again), prefButtons() (new look
     and sound buttons for the bar). */
  function create(ctx) {
    const status = ctx.status();
    const here = hereId(status);
    const first = status.chapters.flatMap((chapter) => chapter.levels)[0];
    let chosen = here || (first ? first.id : null);
    const card = chosen && el("div", { class: "mission-card px", role: "region", "aria-label": "Chosen mission" });

    function choose(id) {
      chosen = id;
      card.replaceChildren(...cardParts(status, id));
      for (const button of element.querySelectorAll(".node")) button.classList.toggle("is-selected", button.dataset.level === id);
    }

    const element = el("div", { class: "starmap" },
      head(),
      bar(status, ctx.prefButtons),
      el("div", { class: "sectors" }, status.chapters.map((chapter, index) => sector(chapter, index, { here, onChoose: choose }))),
      el("footer", { class: "map-foot" }, el("button", { type: "button", class: "btn btn-quiet btn-small erase", onclick: () => erase(ctx) }, "Erase all progress…")),
      card,
    );
    if (chosen) choose(chosen);
    return { element };
  }

  return { create };
})();
