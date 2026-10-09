"use strict";

/*
 * The level screen: a head with the way back to the map, the mission's number, title and command,
 * the commands typed against the par, the stars still in play, Intro (the level's scene again)
 * and Restart; the views across the top, the mission panel, Rama's comms line and the terminal;
 * and, once the mission is solved, the completion band and the dock at the bottom. The views are
 * the view ladder's (docs/drafts/chapters-5-9.md): your station (or the crew view, in a level with
 * a teammate) shows the four zones; history shows the chart alone, the vault and the mothership;
 * two sides open each conflicted file like a book under the strip, and in a crew level flatten
 * Alex's station into the band along the top; the black
 * box frames the places Git keeps, the workshop outside (in a crew level your row alone, Alex in
 * the band). In a level that shows it, the black
 * box's tape of HEAD's moves runs under history and the black box. A level opens on its main view; a view not born yet is
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
 * view-tabs.js, strip.js, sides.js, tape.js, births.js, pictures.js (with the pictures it draws)
 * field-guide.js (with its art and text), keep-panel.js and merge-tool.js. A level with teaching pictures shows them in place
 * of the zones, the strips and the tab row.
 * While the game's merge tool waits in the terminal (`git mergetool`), its panel (merge-tool.js)
 * stands above the terminal, whatever the view; Rama says what it is when it opens, the first
 * time with git's words for the two sides, and says so if the terminal restarts under it.
 * Defines one global, LevelScreen.
 */

/* global Dom, Strings, ArtSprites, Progress, Polling, Zones, ZonePanel, Mission, Comms, Completion, ScenePlayer, MomentLayer, ViewTabs, Strip, Sides, Tape, ViewBirth, FieldGuide, Pictures, MergeTool */
/* exported LevelScreen */

const LevelScreen = (function () {
  const { el } = Dom;
  const { t } = Strings;
  /* The views the page draws so far; a level whose main view is another opens on your station. */
  const DRAWN = ["station", "crew", "history", "sides", "blackbox"];
  /* The views the black box's tape runs under, in a level that shows it. */
  const TAPED = ["history", "blackbox"];
  /* The views that leave your station's strip out: those that show it unfolded, and history, which
     shows the chart alone (the tabs lead back to the stations). */
  const UNSTRIPPED = ["station", "crew", "blackbox", "history"];
  /* The views and pictures that grow downward: on a wide screen they stand in a tall column beside
     the mission and the terminal. A challenge's chart is read against the chain beside it, so that
     pair keeps the width across the top. */
  const COLUMN_VIEWS = ["history"];
  const COLUMN_PICTURES = ["chain", "movelog"];
  /* How the zones lay out on each view (zone-panel.js): history is the chart, the black box keeps
     to your row; every other view shows the zones as they are. */
  const ZONE_MODES = { history: "chart", blackbox: "row" };
  /* Where history's two sides stack (orbit.css): in the wide column, and on a narrow screen. */
  const STACKED = ["(min-width: 1100px)", "(max-width: 760px)"];
  const stacked = () => STACKED.some((query) => window.matchMedia(query).matches);
  /* The zones' mode for a view: history stacks its two sides where the screen stacks them. */
  const zoneMode = (view) => (view === "history" && stacked() ? "stack" : ZONE_MODES[view] || "zones");
  /* Solve's pace: how often it looks, and how long a line or a goal may take before it gives up. */
  const POLL_MS = 300;
  const LINE_MS = 20000;
  const GOAL_MS = 8000;
  /* Ctrl-C, as the terminal sends it: the game's merge tool reads it as Cancel. */
  const CTRL_C = "\x03";
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
    ui.guide = el("button", { type: "button", class: "btn guide-open", onclick: () => openGuide(screen) }, el("span", { class: "lbl" }, t("level.guide")));
    ui.solve = el("button", { type: "button", class: "btn solve", hidden: true, title: t("level.solveTip"), onclick: () => solve(screen) }, el("span", { class: "lbl" }, t("level.solve")));
    return el("header", { class: "hud" },
      el("a", { class: "btn", href: "#/", "aria-label": t("level.mapTip") }, ArtSprites.icon("back"), el("span", { class: "lbl" }, t("level.map"))),
      el("div", { class: "hud-title" }, ui.number, ui.name, ui.command),
      ui.commands,
      ui.stars,
      ui.intro,
      ui.guide,
      ui.solve,
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
    const folded = !UNSTRIPPED.includes(view);
    const boxed = view === "blackbox";
    ui.strip.element.hidden = !folded;
    ui.band.element.hidden = !(folded || boxed) || !screen.crew;
    ui.zones.mode(zoneMode(view));
    ui.sides.element.hidden = view !== "sides";
    ui.tape.element.hidden = !screen.taped || !TAPED.includes(view);
    ui.tabs.select(view);
    ui.stage.classList.toggle("is-column", COLUMN_VIEWS.includes(view));
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

  /* The view the level opens on: its main view, or your station when the page does not draw it yet. */
  const opening = (screen) => (DRAWN.includes(screen.level.view) ? screen.level.view : home(screen));

  /* A level with teaching pictures shows them in place of the zones, the strips and the tab row. */
  function openPictures(screen) {
    const { ctx, ui, level } = screen;
    screen.pictures = Pictures.create(level.pictures, { challenge: level.challenge, target: level.target, timers: ctx.timers });
    ui.tabs.element.hidden = true;
    ui.sky.dataset.view = "pictures";
    ui.sky.replaceChildren(screen.pictures.element, ui.moments.element);
    ui.stage.classList.toggle("is-column", COLUMN_PICTURES.includes(level.pictures.large) && !level.target);
  }

  /* What the current goal asks to look at. */
  const looked = ({ level, state }) => (state.step < level.steps.length ? level.steps[state.step].look : []);

  /* Whether a view shows Alex's band: the folded views, and the black box. */
  const showsBand = (view) => !UNSTRIPPED.includes(view) || view === "blackbox";

  /* The births the level waits for, in order: its main view's, the crew band the first time a
     crew level opens on a view that shows it (once the crew view was born), and the tape in a level that
     shows it. */
  function awaited({ level, seen }, unborn) {
    const births = [];
    if (unborn && ViewBirth.has(level.view)) births.push(level.view);
    if (showsBand(level.view) && seen.includes("crew") && !seen.includes("band")) births.push("band");
    if (level.tape && !seen.includes("tape")) births.push("tape");
    return births;
  }

  /* The level's main view. One not born yet with a birth to play waits on your station for it;
     one the page does not draw yet opens on your station. */
  function openView(screen) {
    const { level } = screen;
    screen.seen = [...level.views_seen];
    const unborn = DRAWN.includes(level.view) && !screen.seen.includes(level.view);
    screen.births = awaited(screen, unborn);
    screen.taped = level.tape && screen.seen.includes("tape");
    drawTabs(screen);
    if (unborn && !screen.births.includes(level.view)) born(screen, level.view);
    show(screen, screen.births.includes(level.view) ? home(screen) : opening(screen));
  }

  /* A birth in place (the tape) leaves the view as it is; the others end on the level's own. */
  async function birth(screen, view) {
    const { ctx, ui } = screen;
    if (view === "tape") screen.taped = true;
    show(screen, screen.view);
    screen.bearing = true;
    await ViewBirth.play(view, { sky: ui.sky, show: (shown) => show(screen, shown), say: (line) => ui.comms.say(line, "info"), reducedMotion: ctx.reducedMotion, timers: ctx.timers });
    screen.bearing = false;
    if (screen.disposed) return;
    born(screen, view);
    show(screen, view === "tape" ? screen.view : opening(screen));
  }

  /* Starts the next waiting birth once the stage, as `reading` reads it, can show it; says whether one started. */
  function bear(screen, reading) {
    const view = screen.births[0];
    if (!view || screen.bearing || !ViewBirth.ready(view, reading)) return false;
    screen.births.shift();
    birth(screen, view);
    return true;
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
    ui.sides = Sides.create();
    ui.tape = Tape.create();
    ui.tabs = ViewTabs.create({ tabs: [], current: "station", onPick: () => {} });
    ui.comms = Comms.create();
    ui.tool = MergeTool.create({
      timers: screen.ctx.timers,
      onWrite: ({ file, read, choices }) => screen.ctx.game.resolve({ file, read, choices }),
      onCancel: () => screen.ctx.terminal.keys(CTRL_C),
      onOpen: () => toolOpened(screen),
      onClose: (why) => why === "terminal" && screen.ui.comms.say(t("tool.hungUp"), "warn"),
    });
    ui.mission = el("aside", { class: "mission px", "aria-label": t("mission.label") }, el("p", {}, t("level.loading")));
    ui.termcol = el("div", { class: "termcol" }, ui.comms.element, ui.tool.element);
    ui.sky = el("div", { class: "sky" }, ui.band.element, ui.strip.element, ui.sides.element, ui.zones.element, ui.tape.element, ui.moments.element);
    ui.stage = el("main", { class: "stage" }, el("div", { class: "views" }, ui.tabs.element, ui.sky), ui.mission, ui.termcol);
    screen.element.replaceChildren(hud(screen), ui.stage);
    show(screen, "station");
  }

  /* The merge tool opened: Rama says what it is, and the first time ever what git calls the two sides. */
  function toolOpened(screen) {
    const first = !screen.seen.includes("mergetool");
    screen.ui.comms.say(first ? `${t("tool.opened")} ${t("tool.localRemote")}` : t("tool.opened"), "info");
    if (!first) return;
    screen.seen.push("mergetool");
    screen.ctx.game.view("mergetool").catch((error) => expected(screen, error) || Promise.reject(error));
  }

  /* Dev mode's solve answers the merge panel as the solution says, once the tool waits for a file
     the observation has read. */
  async function pick(screen, marked) {
    const path = screen.ui.tool.path();
    const choices = screen.picks && path && screen.picks[path];
    const file = choices && !screen.picked.includes(path) && marked.find((entry) => entry.path === path);
    if (!file) return;
    screen.picked.push(path);
    await screen.ctx.game.resolve({ file: path, read: file.read, choices });
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

  /* The field guide over the level, in a modal dialog: the level, its watch and its terminal
     session carry on under it, and Escape or its close button returns to them as they were. */
  function openGuide(screen) {
    if (screen.guide) return;
    const dialog = el("dialog", { class: "guide-overlay", "aria-label": t("level.guide") });
    dialog.append(FieldGuide.create(screen.ctx, { onClose: () => dialog.close() }).element);
    dialog.addEventListener("close", () => {
      dialog.remove();
      screen.guide = null;
    });
    screen.ctx.page.body.append(dialog);
    dialog.showModal();
    screen.guide = dialog;
  }

  /* Waits until `done()` holds, looking every POLL_MS on the screen's timers, for at most `ms`;
     says whether it came to hold. */
  async function until(screen, done, ms) {
    const wait = () => new Promise((resolve) => screen.ctx.timers.setTimeout(resolve, POLL_MS));
    for (let waited = 0; waited < ms && !screen.disposed; waited += POLL_MS) {
      if (await done()) return true;
      await wait();
    }
    return false;
  }

  /* Runs a line in the terminal and waits for the tick that is told it, so the goal it meets has
     passed before the next line runs; false when no tick ever is. */
  async function runLine(screen, line) {
    const before = screen.toldLines;
    screen.ctx.terminal.run(line);
    return until(screen, async () => screen.toldLines > before || screen.finished, LINE_MS);
  }

  async function answerStep(screen, step, solution) {
    const value = step.kind === "read" ? null : solution.answers[step.id];
    await send(screen, () => screen.ctx.game.step(value), stepped);
  }

  /* The current goal when it asks rather than watches, or null. */
  const asking = ({ level, state, finished, disposed }) => {
    const step = !finished && !disposed && state.step < level.steps.length ? level.steps[state.step] : null;
    return step && step.kind !== "watch" ? step : null;
  };

  /* Meets the goals that ask while one is current and its answer is known, so a prediction comes
     before the lines it predicts. The answers are read again each time, since some only exist
     once lines have run (a clone's commit count). False when a goal answered never passes. */
  async function answerAsked(screen) {
    const { ctx, levelId, state } = screen;
    let step = asking(screen);
    while (step) {
      const { solution } = await ctx.game.level(levelId);
      if (step.kind !== "read" && (solution.answers[step.id] ?? null) === null) break;
      const at = state.step;
      await answerStep(screen, step, solution);
      if (!(await until(screen, async () => state.step > at || screen.finished, GOAL_MS))) return false;
      step = asking(screen);
    }
    return true;
  }

  /* Runs the lines in order, each after the goals that ask before it; stops at a line no tick is
     told, at a goal that never passes, or once the level is left. */
  async function runLines(screen, lines) {
    for (const line of lines) {
      if (!(await answerAsked(screen)) || !(await runLine(screen, line))) return false;
    }
    return true;
  }

  /* The goals still open, met in order with the solution's answers; a watch goal is left to the
     polling, which passes it once its lines have run. Then the level's own question. */
  async function answerGoals(screen, solution) {
    const { level, state, ctx } = screen;
    while (!screen.finished && !screen.disposed && state.step < level.steps.length) {
      const at = state.step;
      const step = level.steps[at];
      if (step.kind !== "watch") await answerStep(screen, step, solution);
      if (!(await until(screen, async () => state.step > at || screen.finished, GOAL_MS))) return;
    }
    if (level.question.length && !screen.finished && !screen.disposed) await send(screen, () => ctx.game.check(solution.answer, false), checked);
  }

  /* Dev mode: plays the level from its solution, as a player would. */
  async function solve(screen) {
    const { ctx, levelId, ui } = screen;
    ui.solve.disabled = true;
    const { solution } = await ctx.game.level(levelId);
    screen.picks = solution.picks;
    screen.picked = [];
    const ran = await runLines(screen, solution.lines);
    if (ran) await answerGoals(screen, (await ctx.game.level(levelId)).solution);
    ui.solve.disabled = false;
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
     again, and a moment or a view's birth holds it while it plays, unless newer reactions have
     taken the line (a birth that starts after them, `fresh`, speaks last). Typing again also frees
     the met goal's note. */
  function keeping(screen, { commands, reactions }, fresh) {
    if (commands.length || reactions.length) {
      screen.held = reactions.some(kept);
      screen.metNote = false;
    }
    const playing = screen.bearing || screen.ui.moments.showing();
    return screen.held || fresh || (playing && !reactions.length);
  }

  /* Whether HEAD has moved since the level was first looked at: its newest move is another. */
  function moved(screen, reflog) {
    const newest = reflog.length ? `${reflog[0].new} ${reflog[0].message}` : "";
    if (screen.firstMove === null) screen.firstMove = newest;
    return newest !== screen.firstMove;
  }

  /* The stage drawn from an observation: the zones, the strips, the two sides, the tape and
     whether a teammate is on it; returns the stage as Zones.read reads it, and whether HEAD moved. */
  function stage(screen, observation) {
    const { ui } = screen;
    if (screen.pictures) {
      screen.pictures.update(observation, { look: looked(screen), passed: screen.state.done });
      return { moved: false };
    }
    ui.zones.update(observation);
    const reading = Zones.read(observation);
    ui.strip.update(reading);
    if (reading.crew) ui.band.update(reading.crew);
    ui.sides.update(observation.conflicts);
    ui.tape.update(observation.reflog, observation.ghosts);
    crewed(screen, observation);
    return { ...reading, moved: moved(screen, observation.reflog) };
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
      const reading = stage(screen, observation);
      screen.ui.tool.update({ person: "you", marked: observation.marked, texts: observation.texts });
      await pick(screen, observation.marked);
      measureTerminal(screen);
      if (screen.offline) screen.ui.comms.say(t(SAY.back), "info");
      screen.offline = false;
      react(screen, observation.reactions);
      moments(screen, observation.reactions);
      if (observation.commands.length && !observation.reactions.length && predicting(screen)) screen.ui.comms.say(t(SAY.predictFirst), "info");
      const fresh = bear(screen, reading);
      echo(screen, observation.commands);
      if (observation.commands.length) await recount(screen);
      const keep = keeping(screen, observation, fresh);
      if (plan.watchStep) stepped(screen, await game.step(null), { watched: true, keep });
      if (plan.autoCheck && !screen.finished) checked(screen, await game.check(null, true), { auto: true, keep });
      screen.toldLines += observation.commands.length;
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
    ui.solve.hidden = !ctx.status().dev;
    ui.restart.disabled = false;
    drawHud(screen);
    if (level.pictures) openPictures(screen);
    else openView(screen);
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
    ctx.terminal.attach(ui.termcol, { title: (title, at) => ui.tool.title(title, at), closed: () => ui.tool.closed() });
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
     reducedMotion, terminal ({attach(host, {title(title, at), closed()}), detach(), type(text),
     run(line), keys(raw)}). */
  function create(ctx, levelId) {
    const screen = { ctx, levelId, picks: null, picked: [], level: null, state: null, number: "", shownStars: null, view: "station", seen: [], crew: false, births: [], bearing: false, taped: false, firstMove: null, guide: null, pictures: null, toldLines: 0, held: false, metNote: false, mission: null, poller: null, finished: false, offline: false, attached: false, disposed: false, ui: {} };
    screen.element = el("div", { class: "level-screen" });
    layout(screen);
    /* A screen that crosses a width where history stacks redraws the view it is on. */
    const widths = STACKED.map((query) => window.matchMedia(query));
    const restack = () => screen.state && !screen.pictures && show(screen, screen.view);
    widths.forEach((width) => width.addEventListener("change", restack));
    load(screen);
    return {
      element: screen.element,

      dispose() {
        screen.disposed = true;
        widths.forEach((width) => width.removeEventListener("change", restack));
        stop(screen);
        if (screen.guide) screen.guide.close();
        if (screen.attached) ctx.terminal.detach();
      },
    };
  }

  return { create };
})();
