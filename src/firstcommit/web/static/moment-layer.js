"use strict";

/*
 * The layer over the zones where a reaction's moment plays (art-moments.js), captioned in the
 * page's language. Each moment plays once while the layer lives, since it is one-time; the layer
 * covers the zones until the moment is over, or until a click puts it away. Needs dom.js,
 * strings.js and art-moments.js. Defines one global, MomentLayer.
 *
 * create({reducedMotion, timers})
 *                         {element, play(name)}: the layer, hidden until a moment plays; under
 *                         reduced motion a moment is its still frame, for as long as it lasts.
 *                         The moments are timed on `timers` (window unless given). showing() says
 *                         whether a moment is on the layer; idle() is a promise that resolves once
 *                         none is.
 */

/* global Dom, Strings, ArtMoments */
/* exported MomentLayer */

const MomentLayer = (function () {
  const { el } = Dom;
  const { t, group } = Strings;

  /* Every what-if shares its heading; the rest are the moment's own. */
  const captions = (name) => ({ whatIf: t("moment.whatIf"), ...group(`moment.${name}.`) });

  function create({ reducedMotion = true, timers = window } = {}) {
    const played = new Set();
    const element = el("div", { class: "moment-layer", hidden: true, onclick: () => hide() });
    let shown = Promise.resolve();
    let release = () => {};

    function hide() {
      element.hidden = true;
      element.replaceChildren();
      release();
    }

    return {
      element,

      play(name) {
        if (played.has(name)) return;
        played.add(name);
        release();
        shown = new Promise((resolve) => (release = resolve));
        const moment = ArtMoments.play(name, { captions: captions(name), reducedMotion, timers });
        element.replaceChildren(moment.element);
        element.hidden = false;
        moment.finished.then(() => {
          if (element.firstChild === moment.element) hide();
        });
      },

      showing: () => !element.hidden,

      idle: () => shown,
    };
  }

  return { create };
})();
