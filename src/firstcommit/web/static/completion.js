"use strict";

/*
 * A mission's completion, as the design shows it: a short band across the screen with sparks,
 * then the dock at the bottom with the stars won, the lesson, the new command card and the ways
 * on (Retry, Map, Next), so the terminal and the zones stay in view. Needs dom.js, markup.js,
 * art-sprites.js and art-sky.js. Defines one global, Completion.
 *
 * band({title, subtitle, stars, timers, reducedMotion}) plays the band and resolves when it has
 *   gone (after BAND_MS, or at once on a click); with reduced motion it shows nothing.
 * lost({message, onRetry}) builds the failure that takes the dock's place when the player's work
 *   is gone for good: the game's message, Retry and Map; no stars, no lesson.
 * dock({title, stars, lesson, reward, card, challenge, next, onRetry}) builds the dock (gold for a
 *   challenge): `lesson` is the
 *   game's blocks or null, `reward` a line on what this play paid or null, `card` the new command card
 *   (CommandCard) or null, `next` {href, title} or null.
 */

/* global Dom, Markup, ArtSprites, ArtSky */
/* exported Completion */

const Completion = (function () {
  const { el } = Dom;
  const BAND_MS = 1750;

  function band({ title, subtitle, stars, timers, reducedMotion }) {
    if (reducedMotion) return Promise.resolve();
    const layer = el("div", { class: "band-layer", "aria-hidden": "true" },
      el("div", { class: "band-veil" }),
      ArtSky.sparks(title),
      el("div", { class: "band" }, el("h2", {}, title), el("div", { class: "band-stars" }, ArtSprites.stars(stars, { pop: true })), el("small", {}, subtitle)),
    );
    document.body.append(layer);
    return new Promise((resolve) => {
      const end = () => {
        timers.clearTimeout(timer);
        layer.remove();
        resolve();
      };
      const timer = timers.setTimeout(end, BAND_MS);
      layer.addEventListener("click", end);
    });
  }

  function dock({ title, stars, lesson, reward = null, card = null, challenge = false, next, onRetry }) {
    return el("div", { class: challenge ? "dock px is-challenge" : "dock px", role: "status", "aria-live": "polite" },
      el("div", { class: "dock-stars" }, ArtSprites.stars(stars)),
      el("div", { class: "dock-info" },
        el("b", { class: "dock-title" }, title),
        el("div", { class: "dock-lesson" }, lesson ? Markup.render(lesson) : el("p", {}, "This mission's lesson is not available.")),
        reward && el("small", { class: "dock-xp" }, reward),
        card && el("small", { class: "dock-card" }, "New card in your collection: ", el("code", {}, card.command)),
      ),
      el("div", { class: "dock-actions" },
        el("button", { type: "button", class: "btn", onclick: () => onRetry() }, "Retry"),
        el("a", { class: next ? "btn" : "btn btn-primary", href: "#/" }, "Map"),
        next && el("a", { class: "btn btn-primary", href: next.href, title: next.title }, "Next mission"),
      ),
    );
  }

  function lost({ message, onRetry }) {
    return el("div", { class: "dock px is-lost", role: "alert" },
      el("div", { class: "dock-stars" }),
      el("div", { class: "dock-info" },
        el("b", { class: "dock-title" }, "This work is lost"),
        el("div", { class: "dock-lesson" }, Markup.render(message)),
      ),
      el("div", { class: "dock-actions" },
        el("button", { type: "button", class: "btn btn-primary", onclick: () => onRetry() }, "Retry"),
        el("a", { class: "btn", href: "#/" }, "Map"),
      ),
    );
  }

  return { band, dock, lost, BAND_MS };
})();
