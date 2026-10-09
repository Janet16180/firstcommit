"use strict";

/*
 * Watching the lab while the player works. Defines one global, Polling.
 *
 * plan(steps, active, challenge) says what to ask the server on each tick: always the live lab
 * (observe); the current quest step while it is a watch step (it passes by itself once the lab
 * shows the step was done), or, in a challenge, the goals not met yet, whatever their order; and the level itself, as an automatic check, when the server says it may be
 * (ActiveView's auto_check). Which step is current and whether anything passed is the server's
 * to say.
 *
 * start({tick, intervalMs, timers, page}) runs `tick` at once and then `intervalMs` after each
 * tick has finished, so ticks never overlap. It rests while the page is hidden and ticks again
 * as soon as it is shown. A tick that throws stops it (the error surfaces as an unhandled
 * rejection); the tick handles the errors it expects.
 */

/* exported Polling */

const Polling = (function () {
  function plan(steps, active, challenge = false) {
    const current = active.step < active.steps ? steps[active.step] : null;
    const watching = challenge ? current !== null : Boolean(current && current.kind === "watch");
    return { observe: true, watchStep: watching, autoCheck: active.auto_check };
  }

  function start({ tick, intervalMs = 1500, timers = window, page = document }) {
    let stopped = false;
    let running = false;
    let timer = null;

    async function run() {
      timer = null;
      running = true;
      await tick();
      running = false;
      schedule();
    }

    function schedule() {
      if (!stopped && !page.hidden) timer = timers.setTimeout(run, intervalMs);
    }

    function onVisibility() {
      if (stopped || page.hidden || running || timer !== null) return;
      run();
    }

    page.addEventListener("visibilitychange", onVisibility);
    run();
    return {
      stop() {
        stopped = true;
        timers.clearTimeout(timer);
        timer = null;
        page.removeEventListener("visibilitychange", onVisibility);
      },
    };
  }

  return { plan, start };
})();
