"use strict";

/*
 * Rama's comms line above the terminal: Rama, and one thing Rama says, with a mood ("info",
 * "ok", "warn" or "err") that colours the line. What Rama says comes from the game (a step's or
 * a check's message, and later the reactions to typed lines); this only shows it. Needs dom.js, strings.js,
 * markup.js and art-sprites.js. Defines one global, Comms.
 */

/* global Dom, Strings, Markup, ArtSprites */
/* exported Comms */

const Comms = (function () {
  const { el } = Dom;
  const MOODS = ["info", "ok", "warn", "err"];

  function create() {
    const text = el("div", { class: "comms-text" });
    const element = el("div", { class: "comms px", "data-mood": "info", "aria-live": "polite" },
      ArtSprites.rama({ size: "comms" }),
      el("div", {}, el("span", { class: "comms-who" }, Strings.t("comms.who")), text),
    );
    let said = null;

    return {
      element,

      /* `words` is plain text or the game's blocks. */
      say(words, mood = "info") {
        if (!MOODS.includes(mood)) throw new RangeError(`unknown mood: ${mood}`);
        const key = JSON.stringify([words, mood]);
        if (key === said) return;
        said = key;
        element.dataset.mood = mood;
        text.replaceChildren(...(typeof words === "string" ? [el("p", {}, words)] : Markup.render(words)));
      },
    };
  }

  return { create };
})();
