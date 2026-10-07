"use strict";

/*
 * The level screen: a head with the way back to the map and a restart, the four zones across the
 * top, the mission panel, Rama's comms line and the terminal; and, once the mission is solved, the
 * completion band and the dock at the bottom. Opening a mission that is not in progress starts it.
 * It keeps no game state of its own: the step, the hints and whether the mission is solved come
 * from the server's replies, and the page polls the lab while the player works (poll.js).
 * Expected failures are handled here, by HTTP status: 404 means there is no such level, 409 that
 * it is no longer in progress (solved or ended from the command line or another tab), 0 that the
 * server did not answer. Anything else is a bug and is left to surface. Needs dom.js, markup.js,
 * art-sprites.js, progress.js, poll.js, zone-panel.js, mission.js, comms.js and completion.js.
 * Defines one global, LevelScreen.
 *
 * Waiting for fields of docs/briefs/ORBIT.md (marked ORBIT-GAP below): the command label, the
 * stars in play and the commands typed in the head, the scene and its Intro button, and Rama's
 * reactions to typed lines.
 */

/* global Dom, ArtSprites, Progress, Polling, ZonePanel, Mission, Comms, Completion */
/* exported LevelScreen */

const LevelScreen = (function () {
  const { el } = Dom;
  const SAY = {
    preparing: "Preparing your practice repository…",
    start: "Read the goals and type your first command in the terminal.",
    down: "The game server is not answering. Is it still running in your terminal?",
    back: "The game server is answering again.",
    hint: "I left a hint in the mission panel.",
    ended: "This mission is no longer in progress: it was ended from the command line or in another tab. Restart it to play again.",
  };

  function hud(screen) {
    screen.ui.number = el("span", { class: "hud-num" });
    screen.ui.name = el("b", { class: "hud-name" });
    screen.ui.restart = el("button", { type: "button", class: "btn restart", disabled: true, onclick: () => restart(screen) }, ArtSprites.icon("restart"), el("span", { class: "lbl" }, "Restart"));
    /* ORBIT-GAP(command, commands, stars, scene): the command label after the name, the commands
       typed against the par, the stars still in play, and the Intro button that replays the scene. */
    return el("header", { class: "hud" },
      el("a", { class: "btn", href: "#/", "aria-label": "Back to the map" }, ArtSprites.icon("back"), el("span", { class: "lbl" }, "Map")),
      el("div", { class: "hud-title" }, screen.ui.number, screen.ui.name),
      screen.ui.restart,
    );
  }

  function layout(screen) {
    const { ui } = screen;
    ui.zones = ZonePanel.create();
    ui.comms = Comms.create();
    ui.mission = el("aside", { class: "mission px", "aria-label": "Mission" }, el("p", {}, "Loading the mission…"));
    ui.termcol = el("div", { class: "termcol" }, ui.comms.element);
    ui.stage = el("main", { class: "stage" }, ui.zones.element, ui.mission, ui.termcol);
    screen.element.replaceChildren(hud(screen), ui.stage);
  }

  function missing(screen) {
    screen.element.replaceChildren(el("section", { class: "panel narrow" }, el("h1", {}, "There is no mission here"), el("p", {}, "There is no mission with this address. ", el("a", { href: "#/" }, "Back to the map"))));
  }

  function stop(screen) {
    screen.finished = true;
    if (screen.poller) screen.poller.stop();
  }

  /* Handles the failures a request can be expected to meet; returns false for any other. */
  function expected(screen, error) {
    if (error.status === 409 && !screen.finished) endedElsewhere(screen);
    if (error.status === 0) {
      screen.offline = true;
      screen.ui.comms.say(SAY.down, "err");
    }
    return error.status === 409 || error.status === 0;
  }

  async function send(screen, request, handle) {
    screen.mission.busy(true);
    try {
      handle(screen, await request());
    } catch (error) {
      if (!expected(screen, error)) throw error;
    } finally {
      screen.mission.busy(false);
    }
  }

  /* A quest step's result. A watch step polled without the player shows its message quietly: it
     says what to do next, it is not the player's mistake. */
  function stepped(screen, result, watched = false) {
    const { ui, state, ctx } = screen;
    if (!result.correct) {
      ui.comms.say(result.message, watched ? "info" : "err");
      if (!watched) ctx.sound.play("wrong");
      return;
    }
    state.step = result.step;
    state.auto_check = result.quest_done;
    ui.comms.say(result.message, "ok");
    ctx.sound.play(watched ? "step" : "correct");
    screen.mission.setStep(state.step);
  }

  /* A check's result. An automatic check that does not solve says nothing: the player did not ask. */
  function checked(screen, result, auto = false) {
    if (result.solved) {
      if (screen.finished) return;
      stop(screen);
      won(screen, result.debrief);
    } else if (!auto) {
      screen.ui.comms.say(result.message, "err");
      screen.ctx.sound.play("wrong");
    }
  }

  function hinted(screen, hint) {
    screen.state.hints = hint.used;
    screen.mission.addHint(hint);
    screen.ui.comms.say(SAY.hint, "info");
    screen.ctx.sound.play("hint");
  }

  async function won(screen, debrief) {
    const { ctx, levelId } = screen;
    screen.mission.solved();
    const status = await ctx.refresh();
    const next = Progress.nextLevel(status.chapters, levelId);
    ctx.sound.play("celebrate");
    /* ORBIT-GAP(stars): the band and the dock show the stars won. */
    await Completion.band({ title: "Mission complete", subtitle: `Mission ${screen.number}: ${screen.level.title}`, timers: ctx.timers, reducedMotion: ctx.reducedMotion });
    const dock = Completion.dock({
      title: `Mission complete: mission ${screen.number}`,
      lesson: debrief,
      next: next && { href: `#/level/${encodeURIComponent(next.id)}`, title: next.title },
      onRetry: () => restart(screen),
    });
    screen.element.append(dock);
    screen.element.classList.add("is-docked");
    screen.element.style.setProperty("--dock-h", `${dock.offsetHeight || 120}px`);
  }

  /* The mission stopped being in progress elsewhere: a solve shows the dock with the lesson of its
     last play, anything else is said on Rama's line. */
  async function endedElsewhere(screen) {
    stop(screen);
    const status = await screen.ctx.refresh();
    const payout = status.last_payout;
    if (payout && payout.level === screen.levelId) won(screen, (await screen.ctx.game.level(screen.levelId)).debrief);
    else screen.ui.comms.say(SAY.ended, "warn");
  }

  async function restart(screen) {
    stop(screen);
    screen.ui.restart.disabled = true;
    try {
      await screen.ctx.game.start(screen.levelId);
    } catch (error) {
      if (error.status !== 0) throw error;
      screen.ui.comms.say(SAY.down, "err");
      return;
    }
    screen.ctx.reload();
  }

  /* Tells the stylesheet where the terminal's column starts on the page, so the terminal can
     reach the bottom of the window; the zones above it grow as the repository fills. */
  function measureTerminal(screen) {
    const top = screen.ui.termcol.getBoundingClientRect().top + (window.scrollY || 0);
    screen.element.style.setProperty("--term-top", `${Math.round(top)}px`);
  }

  async function tick(screen) {
    const { game } = screen.ctx;
    try {
      const plan = Polling.plan(screen.level.steps, screen.state);
      const observation = await game.observe();
      screen.ui.zones.update(observation);
      measureTerminal(screen);
      /* ORBIT-GAP(reactions): Rama's reactions to the typed lines (observation.reactions) go on the comms line. */
      if (screen.offline) screen.ui.comms.say(SAY.back, "info");
      screen.offline = false;
      if (plan.watchStep) stepped(screen, await game.step(null), true);
      if (plan.autoCheck && !screen.finished) checked(screen, await game.check(null, true), true);
    } catch (error) {
      if (!expected(screen, error)) throw error;
    }
  }

  function play(screen, active) {
    const { ctx, ui, level } = screen;
    const { game } = ctx;
    screen.state = { ...active };
    screen.number = Progress.missionNumber(ctx.status().chapters, screen.levelId)?.number || "";
    ui.number.textContent = `Mission ${screen.number}`;
    ui.name.textContent = level.title;
    ui.restart.disabled = false;
    screen.mission = Mission.create({
      level,
      active,
      onAnswer: (answer) => send(screen, () => game.step(answer), stepped),
      onContinue: () => send(screen, () => game.step(null), stepped),
      onCheck: (answer) => send(screen, () => game.check(answer, false), checked),
      onHint: () => send(screen, () => game.hint(), hinted),
      onType: ctx.terminal.type,
    });
    ui.mission.replaceWith(screen.mission.element);
    ui.mission = screen.mission.element;
    ui.comms.say(SAY.start);
    ctx.terminal.attach(ui.termcol);
    screen.attached = true;
    measureTerminal(screen);
    screen.poller = Polling.start({ tick: () => tick(screen), timers: ctx.timers, page: ctx.page });
  }

  async function load(screen) {
    const { ctx, levelId } = screen;
    const status = ctx.status();
    let active = status.active && status.active.level === levelId ? status.active : null;
    try {
      if (!active) {
        screen.ui.comms.say(SAY.preparing);
        active = await ctx.game.start(levelId);
        await ctx.refresh();
      }
      /* The level's texts are filled from the state of the lab, so they are read after the start. */
      screen.level = await ctx.game.level(levelId);
    } catch (error) {
      if (error.status === 404) return missing(screen);
      if (error.status === 0) return screen.ui.comms.say(SAY.down, "err");
      throw error;
    }
    if (screen.disposed) return null;
    return play(screen, active);
  }

  /* ctx: game, status(), refresh(), reload() (shows this screen again), sound, timers, page,
     reducedMotion, terminal ({attach(host), detach(), type(text)}). */
  function create(ctx, levelId) {
    const screen = { ctx, levelId, level: null, state: null, number: "", mission: null, poller: null, finished: false, offline: false, attached: false, disposed: false, ui: {} };
    screen.element = el("div", { class: "level-screen" });
    layout(screen);
    load(screen);
    return {
      element: screen.element,

      dispose() {
        screen.disposed = true;
        stop(screen);
        if (screen.attached) ctx.terminal.detach();
      },
    };
  }

  return { create };
})();
