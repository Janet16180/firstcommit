"use strict";

/*
 * The map screen: Rama and the game's name, a bar with the stars won, the missions done, the
 * field guide, the cards due and the look and sound buttons, then every chapter as a
 * sector in play order. A sector with missions is a strip of space with its planet and its
 * numbered mission nodes along a route; a chapter with none yet is a sector coming soon.
 * Choosing a node shows its mission on the card at the bottom (its command and best stars),
 * whose button opens the level. Everything comes from firstcommit/game.py's Status. Needs
 * dom.js, strings.js, art-sprites.js, art-sky.js, progress.js and dialog.js. Defines one
 * global, StarMap.
 */

/* global Dom, Strings, ArtSprites, ArtSky, Progress, Dialog */
/* exported StarMap */

const StarMap = (function () {
  const { el, svg } = Dom;
  const { t } = Strings;
  const levelHref = (id) => `#/level/${encodeURIComponent(id)}`;

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
        el("h1", { class: "map-title" }, t("app.title")),
        el("p", { class: "map-lede" }, t("map.lede")),
      ),
    );
  }

  function bar(status, prefButtons) {
    const levels = status.chapters.flatMap((chapter) => chapter.levels);
    const done = levels.filter((level) => level.done).length;
    const stars = levels.reduce((sum, level) => sum + level.stars, 0);
    return el("div", { class: "map-bar" },
      el("span", { class: "counter px stars-won", role: "img", "aria-label": t("map.stars", { stars, total: levels.length * 3 }) }, ArtSprites.star(true), " ", el("b", {}, `${stars}/${levels.length * 3}`)),
      el("span", { class: "counter px" }, `${t("map.missions")} `, el("b", {}, `${done}/${levels.length}`)),
      el("span", { class: "spacer" }),
      el("a", { class: "btn field-guide-open", href: "#/guide" }, t("map.guide")),
      status.cards_due > 0 && el("a", { class: "btn", href: "#/cards" }, t("map.review", { count: status.cards_due })),
      prefButtons(),
    );
  }

  function sectorHead(chapter, index) {
    const id = encodeURIComponent(chapter.id);
    return el("header", { class: "sector-head" },
      el("span", { class: "snum" }, t("map.sector", { number: index + 1 })),
      el("h2", {}, chapter.title),
      el("p", { class: "sector-blurb" }, chapter.blurb),
      chapter.levels.length > 0 && chapter.cards > 0 && el("p", { class: "sector-links" }, el("a", { href: `#/notes/${id}` }, t("map.notes")), el("a", { href: `#/cards/${id}` }, t("map.practise", { count: chapter.cards }))),
    );
  }

  function node(level, point, { number, here, onChoose }) {
    const named = t(level.challenge ? "map.challenge" : "map.mission", { number, title: level.title });
    const label = level.done ? t("map.done", { label: named }) : named;
    return el("button", {
      type: "button",
      class: ["node", level.done && "is-done", level.challenge && "is-boss"].filter(Boolean).join(" "),
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
      return el("section", { class: "sector is-soon" }, sectorHead(chapter, index), el("div", { class: "soon-field" }, t("map.soon")));
    }
    return el("section", { class: "sector" }, sectorHead(chapter, index), field(chapter, index, options));
  }

  function playLabel(level, active) {
    let key = "map.start";
    if (active && active.level === level.id) key = "map.continue";
    else if (level.done) key = "map.again";
    return t(key);
  }

  /* The card's contents for the chosen mission. */
  function cardParts(status, id) {
    const level = Progress.findLevel(status.chapters, id);
    const { sector: number, number: mission } = Progress.missionNumber(status.chapters, id);
    const { active } = status;
    const other = active && active.level !== id ? Progress.findLevel(status.chapters, active.level) : null;
    return [
      el("span", { class: "card-num" }, t(level.challenge ? "map.cardChallenge" : "map.cardMission", { sector: number, number: mission })),
      el("h2", { class: "card-title" }, level.title),
      /* A challenge's command stays hidden until it is solved: it would give the answer away. */
      el("div", { class: "card-meta" }, !(level.challenge && !level.done) && el("code", {}, level.command), ArtSprites.stars(level.stars)),
      el("p", { class: "card-note" }, other ? t("map.ends", { title: other.title }) : ""),
      el("a", { class: "btn btn-primary", href: levelHref(id) }, playLabel(level, active)),
    ];
  }

  async function erase(ctx) {
    const sure = await Dialog.confirm({
      title: t("erase.title"),
      text: t("erase.text"),
      confirm: t("erase.confirm"),
      cancel: t("erase.cancel"),
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
    const card = chosen && el("div", { class: "mission-card px", role: "region", "aria-label": t("map.chosen") });

    function choose(id) {
      chosen = id;
      card.replaceChildren(...cardParts(status, id));
      for (const button of element.querySelectorAll(".node")) button.classList.toggle("is-selected", button.dataset.level === id);
    }

    const element = el("div", { class: "starmap" },
      head(),
      bar(status, ctx.prefButtons),
      el("div", { class: "sectors" }, status.chapters.map((chapter, index) => sector(chapter, index, { here, onChoose: choose }))),
      el("footer", { class: "map-foot" }, el("button", { type: "button", class: "btn btn-quiet btn-small erase", onclick: () => erase(ctx) }, t("map.erase"))),
      card,
    );
    if (chosen) choose(chosen);
    return { element };
  }

  return { create };
})();
