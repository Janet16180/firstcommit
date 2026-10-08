"use strict";

/*
 * The births of the view ladder (docs/drafts/chapters-5-9.md): a new view is born on screen out
 * of one the player knows, in stages, each with Rama's line. A stage puts a view on the stage and
 * an art class on the sky for BIRTH_MS (art-style.css draws the motion); under reduced motion a
 * stage is a still frame held STILL_MS, long enough to read its line. Needs dom.js and
 * strings.js. Defines one global, ViewBirth.
 *
 * has(view)              whether the view (or "band", the crew band) has a birth.
 * ready(view, reading)   whether the stage, as Zones.read reads it, has something to show the
 *                        birth with: history waits for your vault to hold commits, the band for
 *                        a teammate, two sides for a file in conflict; the black box is born as
 *                        its level opens.
 * play(view, {sky, show, say, reducedMotion, timers})
 *                        a promise that resolves once the birth is over; show(view) puts a view on
 *                        the stage ("fold" is your station with the strip above it, "flatten" the
 *                        crew view with the band above it), say(text) gives Rama the line. Timed
 *                        on `timers` (window unless given).
 */

/* global Strings */
/* exported ViewBirth */

const ViewBirth = (function () {
  const { t } = Strings;
  const BIRTH_MS = 1400;
  const STILL_MS = 2600;
  const STAGES = {
    history: [
      { view: "fold", motion: "art-birth-fold", line: "views.born.strip" },
      { view: "history", motion: "art-birth-unroll", line: "views.born.history" },
    ],
    band: [{ view: "flatten", motion: "art-birth-flatten", line: "views.born.band" }],
    sides: [{ view: "sides", motion: "art-birth-book", line: "views.born.sides" }],
    blackbox: [{ view: "blackbox", motion: "art-birth-boundary", line: "views.born.blackbox" }],
  };

  const has = (view) => Object.hasOwn(STAGES, view);

  const READY = {
    history: (reading) => Boolean(reading.vault && reading.vault.length),
    band: (reading) => reading.crew !== null,
    sides: (reading) => reading.workshop.some((file) => file.state === "conflicted"),
    blackbox: () => true,
  };

  const ready = (view, reading) => READY[view](reading);

  async function play(view, { sky, show, say, reducedMotion = true, timers = window }) {
    const wait = (ms) => new Promise((resolve) => timers.setTimeout(resolve, ms));
    sky.style.setProperty("--art-birth", `${BIRTH_MS}ms`);
    for (const stage of STAGES[view]) {
      show(stage.view);
      say(t(stage.line));
      if (!reducedMotion) sky.classList.add(stage.motion);
      await wait(reducedMotion ? STILL_MS : BIRTH_MS);
      sky.classList.remove(stage.motion);
    }
  }

  return { BIRTH_MS, STILL_MS, has, ready, play };
})();
