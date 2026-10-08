"use strict";

/*
 * The level screen: a head with the way back to the map, the mission's number, title and command,
 * the commands typed against the par, the stars still in play, Intro (the level's scene again)
 * and Restart; the views across the top, the mission panel, Rama's comms line and the terminal;
 * and, once the mission is solved, the completion band and the dock at the bottom. The views are
 * the view ladder's (docs/drafts/chapters-5-9.md): your station (or the crew view, in a level with
 * a teammate) shows the four zones; history folds your station into the strip and leaves the
 * vault and the mothership on the stage, and in a crew level flattens Alex's station into the
 * band along the top. A level opens on its main view; a view not born yet is
 * born first (births.js), once the stage has something to show it with, and then marked born.
 * The tab row holds the views born so far.
 * Opening a mission that is not in progress starts it, and a level's scene plays the first time
 * it opens. It keeps no game state of its own: the step, the hints, the commands, the stars and
 * whether the mission is solved come from the server's replies, and the page polls the lab while
 * the player works (poll.js). Rama says what the game says about each typed line (the observation's
 * reactions), and a reaction's moment plays over the zones. Expected failures are handled here, by
 * HTTP status: 404 means there is no such level, 409 that it is no longer in progress (solved or
 * ended from the command line or another tab), 0 that the server did not answer. Anything else is a
 * bug and is left to surface. Needs dom.js, strings.js, markup.js, art-sprites.js, progress.js,
 * poll.js, zones.js, zone-panel.js, mission.js, comms.js, completion.js, scene.js, moment-layer.js,
 * view-tabs.js, strip.js and births.js.
 * Defines one global, LevelScreen.
 */

/* global Dom, Strings, ArtSprites, Progress, Polling, Zones, ZonePanel, Mission, Comms, Completion, ScenePlayer, MomentLayer, ViewTabs, Strip, ViewBirth */
/* exported LevelScreen */

const LevelScreen = (function () {
  const { el } = Dom;
  const { t } = Strings;
  /* The views the page draws so far; a level whose main view is another opens on your station. */
  const DRAWN = ["station", "crew", "history"];
  const SAY = { preparing: "level.preparing", start: "level.start", down: "level.down", back: "level.back", hint: "level.hint", ended: "level.ended", partMet: "level.partMet", predictFirst: "level.predictFirst" };


  function hud(screen) {
    const { ui } = screen;
    ui.number = el("span", { class: "hud-num" });
    ui.name = el("b", { class: "hud-name" });
    ui.command = el("code", { class: "hud-command" });
    ui.commands = el("span", { class: "hud-cmds" });
    ui.stars = el("span", { class: "hud-stars" });
    ui.intro = el("button", { type: "button", class: "btn intro", hidden: true, "aria-label": t("level.introTip"), onclick: () => scene(screen) }, ArtSprites.icon("replay"), el("span", { class: "lbl" }, t("level.intro")));
    ui.restart = el("button", { type: "button", class: "btn restart", disabled: true, onclick: () => restart(screen) }, ArtSprites.icon("restart"), el("span", { class: "lbl" }, t("level.restart")));
    return el("header", { class: "hud" },
      el("a", { class: "btn", href: "#/", "aria-label": t("level.mapTip") }, ArtSprites.icon("back"), el("span", { class: "lbl" }, t("level.map"))),
      el("div", { class: "hud-title" }, ui.number, ui.name, ui.command),
      ui.commands,
      ui.stars,
      ui.intro,
      ui.restart,
    );
  }

  /* The commands typed against the par plus three, and the stars still in play; a lost star shakes. */
  function drawHud(screen) {
    const { ui, state, level } = screen;
    ui.commands.textContent = t("level.commands", { count: state.commands, limit: level.par + 3 });
    const lost = screen.shownStars !== null && state.stars < screen.shownStars;
    screen.shownStars = state.stars;
    ui.stars.replaceChildren(ArtSprites.stars(state.stars, { label: t("level.stars", { count: state.stars }) }));
    ui.stars.classList.toggle("is-lost", lost);
    if (lost) screen.ctx.sound.play("starlost");
  }

  /* The commands and stars as the game now counts them (the level in progress, from the dashboard). */
  async function recount(screen) {
    const status = await screen.ctx.refresh();
    const active = status.active;
    if (!active || active.level !== screen.levelId || screen.finished) return;
    screen.state.commands = active.commands;
    screen.state.stars = active.stars;
    drawHud(screen);
  }

  /* Plays the level's scene; the first time, the game is told it was seen. */
  async function scene(screen) {
    const { ctx, level } = screen;
    await ScenePlayer.play({ scene: level.scene, timers: ctx.timers, reducedMotion: ctx.reducedMotion, sound: ctx.sound });
    if (level.scene_seen) return;
    level.scene_seen = true;
    await ctx.game.scene(screen.levelId);
  }

  /* Your station's view: the crew view in a level with a teammate. */
  const home = (screen) => (screen.crew ? "crew" : "station");

  function show(screen, view) {
    const { ui } = screen;
    screen.view = view;
    ui.sky.dataset.view = view;
    const folded = view !== "station" && view !== "crew";
    ui.strip.element.hidden = !folded;
    ui.band.element.hidden = !folded || !screen.crew;
    ui.tabs.select(view);
    measureTerminal(screen);
  }

  /* The tab row for the views born so far that the page draws, your station's always among them. */
  function drawTabs(screen) {
    const views = ViewTabs.tabs([...screen.seen, home(screen)], screen.crew).filter((view) => DRAWN.includes(view));
    const row = ViewTabs.create({ tabs: views, current: screen.view, onPick: (view) => show(screen, view) });
    screen.ui.tabs.element.replaceWith(row.element);
    screen.ui.tabs = row;
  }

  /* The game is told a view was born, and its tab joins the row. */
  function born(screen, view) {
    screen.seen.push(view);
    screen.ctx.game.view(view);
    drawTabs(screen);
  }

  /* The level's main view. One not born yet with a birth to play waits on your station for it;
     one the page does not draw yet opens on your station. */
  function openView(screen) {
    const { level } = screen;
    screen.seen = [...level.views_seen];
    const drawn = DRAWN.includes(level.view);
    const unborn = drawn && !screen.seen.includes(level.view);
    screen.birth = unborn && ViewBirth.has(level.view) ? level.view : null;
    drawTabs(screen);
    if (unborn && !screen.birth) born(screen, level.view);
    show(screen, drawn && !screen.birth ? level.view : home(screen));
  }

  /* Plays the waiting birth once the stage, as `reading` reads it, can show it. */
  async function bear(screen, reading) {
    const { ctx, ui } = screen;
    const view = screen.birth;
    if (!view || !ViewBirth.ready(view, reading)) return;
    screen.birth = null;
    screen.bearing = true;
    await ViewBirth.play(view, { sky: ui.sky, show: (shown) => show(screen, shown), say: (line) => ui.comms.say(line, "info"), reducedMotion: ctx.reducedMotion, timers: ctx.timers });
    screen.bearing = false;
    if (screen.disposed) return;
    born(screen, view);
    show(screen, view);
  }

  /* The stage follows the level's teammate: your station's view becomes the crew view. */
  function crewed(screen, observation) {
    const crew = observation.teammate !== null;
    if (crew === screen.crew) return;
    const atHome = screen.view === home(screen);
    screen.crew = crew;
    drawTabs(screen);
    show(screen, atHome ? home(screen) : screen.view);
  }

  function layout(screen) {
    const { ui } = screen;
    ui.zones = ZonePanel.create({ reducedMotion: screen.ctx.reducedMotion, timers: screen.ctx.timers });
    ui.moments = MomentLayer.create({ reducedMotion: screen.ctx.reducedMotion, timers: screen.ctx.timers });
    ui.strip = Strip.create({ onExpand: () => show(screen, home(screen)) });
    ui.band = Strip.create({ onExpand: () => show(screen, "crew"), who: "alex" });
    ui.tabs = ViewTabs.create({ tabs: [], current: "station", onPick: () => {} });
    ui.comms = Comms.create();
    ui.mission = el("aside", { class: "mission px", "aria-label": t("mission.label") }, el("p", {}, t("level.loading")));
    ui.termcol = el("div", { class: "termcol" }, ui.comms.element);
    ui.sky = el("div", { class: "sky" }, ui.band.element, ui.strip.element, ui.zones.element, ui.moments.element);
    ui.stage = el("main", { class: "stage" }, el("div", { class: "views" }, ui.tabs.element, ui.sky), ui.mission, ui.termcol);
    screen.element.replaceChildren(hud(screen), ui.stage);
    show(screen, "station");
  }

  function missing(screen) {
    screen.element.replaceChildren(el("section", { class: "panel narrow" }, el("h1", {}, t("level.missingTitle")), el("p", {}, `${t("level.missing")} `, el("a", { href: "#/" }, t("level.backToMap")))));
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
      screen.ui.comms.say(t(SAY.down), "err");
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
     says what to do next, it is not the player's mistake. A passed step's message is said in
     `mood`: pleased for a goal met, neutral for a prediction's reveal (any answer passes). In a
     challenge Rama speaks only of danger and errors, so a met goal is said without its message,
     which could tell what comes next; saying it still clears an error the player has fixed. When
     Rama's line must `keep` what it says about the typed lines, the met goal's message goes under
     the next goal instead, and stays there until the player types again. Work lost for good ends
     the play, whoever asked. */
  function stepped(screen, result, { watched = false, mood = "ok", keep = false } = {}) {
    const { ui, state, ctx } = screen;
    if (result.lost) {
      lostWork(screen, result.message);
      return;
    }
    if (!result.correct && watched && !screen.metNote) screen.mission.note(result.message);
    if (!result.correct && !watched) {
      ui.comms.say(result.message, "err");
      ctx.sound.play("wrong");
    }
    if (!result.correct) return;
    state.step = result.step;
    state.done = result.done;
    state.auto_check = result.quest_done;
    screen.mission.setStep(state.step, state.done);
    const message = screen.level.challenge ? t(SAY.partMet) : result.message;
    screen.metNote = keep;
    if (keep) screen.mission.note(message);
    else ui.comms.say(message, mood);
    ctx.sound.play("goal");
  }

  /* A check's result. A solve says its verdict, so no earlier nudge outlives it, unless Rama's line
     must `keep` what it says about the typed lines; an automatic check that does not solve says
     nothing: the player did not ask. */
  function checked(screen, result, { auto = false, keep = false } = {}) {
    if (result.lost) {
      lostWork(screen, result.message);
    } else if (result.solved) {
      if (screen.finished) return;
      stop(screen);
      if (!keep) screen.ui.comms.say(result.message, "ok");
      won(screen, { debrief: result.debrief, stars: result.stars, card: result.new_card, payout: result.payout });
    } else if (!auto) {
      screen.ui.comms.say(result.message, "err");
      screen.ctx.sound.play("wrong");
    }
  }

  function hinted(screen, hint) {
    screen.state.hints = hint.used;
    screen.mission.addHint(hint);
    screen.ui.comms.say(t(SAY.hint), "info");
    screen.ctx.sound.play("hint");
    return recount(screen);
  }

  /* The player's work is gone for good: the play stops and the game says why, in the dock's
     place, with Retry; a goal's note from before the loss would only contradict it. */
  function lostWork(screen, message) {
    if (screen.finished) return;
    stop(screen);
    screen.mission.clearNote();
    screen.ctx.sound.play("wrong");
    const panel = Completion.lost({ message, onRetry: () => restart(screen) });
    screen.element.append(panel);
    screen.element.classList.add("is-docked");
    screen.element.style.setProperty("--dock-h", `${panel.offsetHeight || 120}px`);
  }

  /* What a solved play paid, in a line for the dock. */
  function rewardLine(payout, hints) {
    let line = t("level.noXp");
    if (payout && payout.xp > 0) line = t("level.xp", { xp: payout.xp });
    else if (hints > 0) line = t("level.noXpHint");
    return line;
  }

  /* A solve: `debrief` (the lesson), `stars` won, the new command `card` or null, the `payout`.
     The band waits for a moment still playing over the zones. */
  async function won(screen, { debrief, stars, card, payout }) {
    const { ctx, levelId } = screen;
    screen.mission.solved();
    await screen.ui.moments.idle();
    const status = await ctx.refresh();
    const next = Progress.nextLevel(status.chapters, levelId);
    ctx.sound.play("complete");
    await Completion.band({ title: t(screen.level.challenge ? "level.challengeComplete" : "level.missionComplete"), subtitle: t("level.subtitle", { number: screen.number, title: screen.level.title }), stars, timers: ctx.timers, reducedMotion: ctx.reducedMotion });
    const dock = Completion.dock({
      title: t(screen.level.challenge ? "level.challengeDone" : "level.missionDone", { number: screen.number }),
      challenge: screen.level.challenge,
      stars,
      lesson: debrief,
      reward: rewardLine(payout, screen.state.hints),
      card,
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
    if (payout && payout.level === screen.levelId) {
      const best = Progress.findLevel(status.chapters, screen.levelId);
      won(screen, { debrief: (await screen.ctx.game.level(screen.levelId)).debrief, stars: best ? best.stars : 0, card: null, payout });
    }
    else screen.ui.comms.say(t(SAY.ended), "warn");
  }

  async function restart(screen) {
    stop(screen);
    screen.ui.restart.disabled = true;
    try {
      await screen.ctx.game.start(screen.levelId);
    } catch (error) {
      if (error.status !== 0) throw error;
      screen.ui.comms.say(t(SAY.down), "err");
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

  /* What Rama says about the lines just typed, oldest first, each text once, in the mood of the newest. */
  function react(screen, reactions) {
    if (!reactions.length) return;
    const said = reactions.filter((reaction, index) => reactions.findIndex((other) => JSON.stringify(other.text) === JSON.stringify(reaction.text)) === index);
    screen.ui.comms.say(said.flatMap((reaction) => reaction.text), reactions[reactions.length - 1].mood);
  }

  /* A reaction a met goal must not talk over: a warning, an error, or one that plays a moment. */
  const kept = (reaction) => reaction.moment !== null || reaction.mood === "warn" || reaction.mood === "err";

  /* Whether Rama's line must keep what it says: a kept reaction holds it until the player types
     again, and a moment or a view's birth holds it while it plays. Typing again also frees the
     met goal's note. */
  function keeping(screen, { commands, reactions }) {
    if (commands.length || reactions.length) {
      screen.held = reactions.some(kept);
      screen.metNote = false;
    }
    return screen.held || screen.bearing || screen.ui.moments.showing();
  }

  function moments(screen, reactions) {
    for (const reaction of reactions) if (reaction.moment) screen.ui.moments.play(reaction.moment);
  }

  /* A blip for the lines just typed, or a buzz when one of them failed: the terminal shows both. */
  function echo(screen, typed) {
    if (typed.some((line) => line.status !== 0)) screen.ctx.sound.play("failed");
    else if (typed.length) screen.ctx.sound.play("command");
  }

  /* Whether the current goal is a prediction: the goals after it are not looked at until it is
     answered, so lines typed meanwhile may get no word from the game. */
  const predicting = ({ level, state }) => state.step < level.steps.length && level.steps[state.step].kind === "choice";

  async function tick(screen) {
    const { game } = screen.ctx;
    try {
      const plan = Polling.plan(screen.level.steps, screen.state, screen.level.challenge);
      const observation = await game.observe();
      screen.ui.zones.update(observation);
      const reading = Zones.read(observation);
      screen.ui.strip.update(reading);
      if (reading.crew) screen.ui.band.update(reading.crew);
      crewed(screen, observation);
      bear(screen, reading);
      measureTerminal(screen);
      if (screen.offline) screen.ui.comms.say(t(SAY.back), "info");
      screen.offline = false;
      react(screen, observation.reactions);
      moments(screen, observation.reactions);
      if (observation.commands.length && !observation.reactions.length && predicting(screen)) screen.ui.comms.say(t(SAY.predictFirst), "info");
      echo(screen, observation.commands);
      if (observation.commands.length) await recount(screen);
      const keep = keeping(screen, observation);
      if (plan.watchStep) stepped(screen, await game.step(null), { watched: true, keep });
      if (plan.autoCheck && !screen.finished) checked(screen, await game.check(null, true), { auto: true, keep });
    } catch (error) {
      if (!expected(screen, error)) throw error;
    }
  }

  function play(screen, active) {
    const { ctx, ui, level } = screen;
    const { game } = ctx;
    screen.state = { ...active };
    screen.number = Progress.missionNumber(ctx.status().chapters, screen.levelId)?.number || "";
    ui.number.textContent = t(level.challenge ? "level.challenge" : "level.mission", { number: screen.number });
    ui.name.textContent = level.title;
    /* A challenge keeps its command hidden until solved once: its card, which names it, is null till then. */
    ui.command.textContent = level.challenge && !level.card ? "" : level.command;
    ui.command.hidden = ui.command.textContent === "";
    screen.element.classList.toggle("is-challenge", level.challenge);
    ui.intro.hidden = level.scene.length === 0;
    ui.restart.disabled = false;
    drawHud(screen);
    openView(screen);
    screen.mission = Mission.create({
      level,
      active,
      onAnswer: (answer) => send(screen, () => game.step(answer), stepped),
      onContinue: () => send(screen, () => game.step(null), stepped),
      onChoose: (value) => send(screen, () => game.step(value), (run, result) => stepped(run, result, { mood: "info" })),
      onCheck: (answer) => send(screen, () => game.check(answer, false), checked),
      onHint: () => send(screen, () => game.hint(), hinted),
      onType: ctx.terminal.type,
    });
    ui.mission.replaceWith(screen.mission.element);
    ui.mission = screen.mission.element;
    ui.comms.say(t(SAY.start));
    ctx.terminal.attach(ui.termcol);
    screen.attached = true;
    measureTerminal(screen);
    /* A level may stage a change right after the page first looks at the lab; looking only once
       the scene is over keeps that change, and its motion, in view. */
    const watch = () => {
      if (!screen.disposed && !screen.finished) screen.poller = Polling.start({ tick: () => tick(screen), timers: ctx.timers, page: ctx.page });
    };
    if (level.scene.length && !level.scene_seen) scene(screen).then(watch);
    else watch();
  }

  async function load(screen) {
    const { ctx, levelId } = screen;
    const status = ctx.status();
    let active = status.active && status.active.level === levelId ? status.active : null;
    try {
      if (!active) {
        screen.ui.comms.say(t(SAY.preparing));
        active = await ctx.game.start(levelId);
        await ctx.refresh();
      }
      /* The level's texts are filled from the state of the lab, so they are read after the start. */
      screen.level = await ctx.game.level(levelId);
    } catch (error) {
      if (error.status === 404) return missing(screen);
      if (error.status === 0) return screen.ui.comms.say(t(SAY.down), "err");
      throw error;
    }
    if (screen.disposed) return null;
    return play(screen, active);
  }

  /* ctx: game, status(), refresh(), reload() (shows this screen again), sound, timers, page,
     reducedMotion, terminal ({attach(host), detach(), type(text)}). */
  function create(ctx, levelId) {
    const screen = { ctx, levelId, level: null, state: null, number: "", shownStars: null, view: "station", seen: [], crew: false, birth: null, bearing: false, held: false, metNote: false, mission: null, poller: null, finished: false, offline: false, attached: false, disposed: false, ui: {} };
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
