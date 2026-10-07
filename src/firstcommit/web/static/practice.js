"use strict";

/*
 * Playing a level: the guided quest, then the challenge, beside the live panel and the
 * terminal. It keeps no game state of its own: the step, the hints and whether the level is
 * solved come from the server's replies, and the page polls the lab while the player works
 * (poll.js). Expected failures are handled here, by HTTP status: 409 means the level is no
 * longer in progress (solved or ended from the command line or another tab), 0 means the server
 * did not answer. Anything else is a bug and is left to surface. The player can fold the
 * instructions away to give the map and the terminal the whole width: a small card over the map
 * then names the current step (and flashes when it changes), and the choice is remembered in
 * storage for the next level. On a playground level the live
 * panel holds the playground (playground.js), whose presses go to the server from here. Needs
 * dom.js, markup.js, map.js, poll.js, dialog.js, live.js, playground.js, quest.js and
 * challenge.js. Defines one global, Practice.
 */

/* global Dom, Dialog, Markup, LivePanel, PlaygroundPanel, Polling, Quest, Challenge */
/* exported Practice */

const Practice = (function () {
  const { el } = Dom;
  const ADVANCE_MS = 1100;
  const FLASH_MS = 2400;
  const FOLD_KEY = "firstcommit.instructions";

  function browserStorage() {
    try {
      return window.localStorage;
    } catch {
      return null;
    }
  }

  /* Whether the player last folded the instructions; blocked storage means open. */
  function readFolded(storage) {
    try {
      return Boolean(storage) && storage.getItem(FOLD_KEY) === "folded";
    } catch {
      return false;
    }
  }

  function saveFolded(storage, folded) {
    try {
      if (storage) storage.setItem(FOLD_KEY, folded ? "folded" : "open");
    } catch {
      /* Blocked storage: the choice lasts until the page closes. */
    }
  }

  function layout(level, live, onLeave, onFold) {
    const parts = {
      body: el("div", { class: "practice-body" }),
      toggle: el("button", { type: "button", class: "btn btn-quiet btn-small side-toggle", "aria-expanded": "true", "aria-controls": "practice-side", title: "Hide the instructions; a small card keeps the current step in view", onclick: onFold }, el("span", { "aria-hidden": "true" }, "«"), " Hide"),
      card: el("aside", { class: "task-card", role: "status", "aria-label": "Current task", hidden: true }),
      offline: el("p", { class: "banner is-warning offline", role: "status", hidden: true }, "The game server is not answering. Is it still running in your terminal?"),
    };
    /* The terminal docks at the bottom of this column: termlab sizes it against its parent. */
    parts.terminalHost = el("section", { class: "practice-main", "aria-label": "Your repository and terminal" }, parts.card, el("div", { class: "practice-live" }, live.element));
    parts.element = el("div", { class: "practice" },
      el("aside", { class: "practice-side", id: "practice-side", "aria-label": "Level" },
        el("header", { class: "practice-head" },
          el("div", { class: "practice-head-row" }, el("p", { class: "kicker" }, level.chapter_title), parts.toggle),
          el("h1", {}, level.title),
        ),
        parts.offline,
        parts.body,
        el("footer", { class: "practice-foot" },
          el("p", { class: "keys" }, "In the terminal, Tab completes names; Shift+Tab leaves it."),
          el("button", { type: "button", class: "btn btn-ghost btn-small leave", onclick: onLeave }, "Leave this level"),
        ),
      ),
      parts.terminalHost,
    );
    return parts;
  }

  /* Everything below works on one `run`: ctx, level, ui, live, state (the ActiveView as the server
     last told it, kept current from step results, plus `finished`), the quest or challenge on
     screen, the poller and the owner's callbacks. */

  function finish(run, callback) {
    if (run.state.finished) return;
    run.state.finished = true;
    run.poller.stop();
    callback();
  }

  /* Handles the failures a request can be expected to meet; returns false for any other. */
  function expected(run, error) {
    if (error.status === 409) finish(run, run.on.ended);
    if (error.status === 0) run.ui.offline.hidden = false;
    return error.status === 409 || error.status === 0;
  }

  async function send(run, part, request, handle) {
    part.busy(true);
    try {
      handle(run, await request());
    } catch (error) {
      if (!expected(run, error)) throw error;
    } finally {
      part.busy(false);
    }
  }

  /* The current task as the folded card shows it: a kicker, the first paragraph, its kind. */
  function currentTask(level, state) {
    if (state.step < state.steps) {
      const item = level.steps[state.step];
      return { kicker: `Step ${state.step + 1} of ${state.steps}`, blocks: item.text, kind: item.kind };
    }
    return { kicker: "The challenge", blocks: level.briefing, kind: "challenge" };
  }

  const OPEN_LABEL = { answer: "Answer", challenge: "Show the challenge" };

  /* Draws the card for the current task. A change of task while folded flashes the card. */
  function drawCard(run) {
    const { ui, level, state } = run;
    const task = currentTask(level, state);
    const changed = run.cardKicker !== null && run.cardKicker !== task.kicker;
    run.cardKicker = task.kicker;
    const continueButton = task.kind === "read" && el("button", {
      type: "button",
      class: "btn btn-primary btn-small task-continue",
      onclick: () => {
        continueButton.disabled = true;
        send(run, run.quest, () => run.ctx.game.step(null), stepped).finally(() => (continueButton.disabled = false));
      },
    }, "Continue");
    ui.card.replaceChildren(
      el("p", { class: "kicker task-kicker" }, task.kicker),
      el("div", { class: "prose task-text", title: Markup.plain(task.blocks.slice(0, 1)) }, Markup.render(task.blocks.slice(0, 1))),
      el("div", { class: "task-actions" },
        continueButton,
        el("button", { type: "button", class: "btn btn-ghost btn-small task-open", onclick: () => fold(run, false) }, el("span", { "aria-hidden": "true" }, "» "), OPEN_LABEL[task.kind] || "Show the steps"),
      ),
    );
    if (changed && run.folded) {
      ui.card.classList.add("is-new");
      run.ctx.timers.setTimeout(() => ui.card.classList.remove("is-new"), FLASH_MS);
    }
  }

  /* Folds or opens the instructions; focus follows to what the player will use next. */
  function fold(run, folded, { save = true, focus = true } = {}) {
    const { ui } = run;
    run.folded = folded;
    ui.element.classList.toggle("is-folded", folded);
    ui.toggle.setAttribute("aria-expanded", folded ? "false" : "true");
    ui.card.hidden = !folded;
    if (save) saveFolded(run.storage, folded);
    if (!focus) return;
    const input = ui.body.querySelector(".step.is-current input");
    const target = folded ? ui.card.querySelector(".task-open") : input || ui.toggle;
    target.focus();
  }

  function showPhase(run) {
    const { ctx, level, state, ui } = run;
    const { game } = ctx;
    if (state.step < state.steps) {
      run.quest = Quest.create({
        steps: level.steps,
        step: state.step,
        onAnswer: (answer) => send(run, run.quest, () => game.step(answer), stepped),
        onContinue: () => send(run, run.quest, () => game.step(null), stepped),
        onType: ctx.terminal.type,
        onCheck: () => send(run, run.quest, () => game.check(null, false), checked),
      });
      ui.body.replaceChildren(run.quest.element);
      drawCard(run);
      return;
    }
    run.quest = null;
    run.challenge = Challenge.create({
      level,
      active: state,
      onCheck: (answer) => send(run, run.challenge, () => game.check(answer, false), checked),
      onHint: () => send(run, run.challenge, () => game.hint(), hinted),
    });
    ui.body.replaceChildren(run.challenge.element);
    drawCard(run);
  }

  /* A quest step's result. A watch step polled without the player shows its message as a quiet
     note until it passes: it says what to do next, it is not the player's mistake. */
  function stepped(run, result, watched = false) {
    const { quest, state, ctx } = run;
    if (!result.correct && watched) quest.note(result.message);
    if (!result.correct && !watched) {
      quest.feedback(result.message, false);
      ctx.sound.play("wrong");
    }
    if (!result.correct) return;
    state.step = result.step;
    state.auto_check = result.quest_done;
    quest.feedback(result.message, true);
    ctx.sound.play(watched ? "step" : "correct");
    ctx.timers.setTimeout(() => {
      if (state.finished) return;
      if (state.step < state.steps && run.quest) {
        run.quest.setStep(state.step);
        drawCard(run);
        return;
      }
      showPhase(run);
      if (!run.folded) run.challenge.element.querySelector(".kicker").focus();
    }, ADVANCE_MS);
  }

  /* A check's result, from the quest or the challenge. A solve also replaces any "not yet" on
     screen, which the player sees again after the celebration. An automatic check that does not
     solve says nothing: the player did not ask, and the challenge already says what is next. */
  function checked(run, result, auto = false) {
    const part = run.challenge || run.quest;
    if (result.solved) {
      part.checkFeedback(result.message, true);
      finish(run, () => run.on.solved(result));
    } else if (!auto) {
      part.checkFeedback(result.message, false);
      run.ctx.sound.play("wrong");
    }
  }

  /* A 409 for a playground button that was off when the press arrived: the level goes on. */
  const offButton = (error) => error.status === 409 && Boolean(error.data) && error.data.kind === "off";

  /* One playground press: the lab drawn as it was just before it (what the terminal changed),
     then as the press left it, played in the pressing person's computer; then its result. */
  async function pressButton(run, person, id) {
    const { playground, live, ctx } = run;
    run.presses += 1;
    playground.busy(true);
    run.pressing = true;
    try {
      const view = await ctx.game.press(person, id);
      live.update(view.before);
      live.update(view.observation, { person });
      playground.result(view);
    } catch (error) {
      if (offButton(error)) playground.refused(error.message);
      else if (!expected(run, error)) throw error;
    } finally {
      run.pressing = false;
      playground.busy(false);
    }
  }

  function hinted(run, hint) {
    run.state.hints = hint.used;
    run.challenge.addHint(hint);
    run.ctx.sound.play("hint");
  }

  async function tick(run) {
    const { game } = run.ctx;
    try {
      const plan = Polling.plan(run.level.steps, run.state);
      const asked = run.presses;
      const observation = await game.observe();
      /* An answer asked for before the last press began, or while one runs, would draw an older
         lab over the press's: it is dropped. */
      if (!run.pressing && asked === run.presses) run.live.update(observation);
      run.ui.offline.hidden = true;
      if (plan.watchStep) stepped(run, await game.step(null), true);
      if (plan.autoCheck && !run.state.finished) checked(run, await game.check(null, true), true);
    } catch (error) {
      if (!expected(run, error)) throw error;
    }
  }

  async function leave(run) {
    const sure = await Dialog.confirm({
      title: "Leave this level?",
      text: "Its practice repository is deleted. You can start the level again later.",
      confirm: "Leave the level",
      cancel: "Keep playing",
    });
    if (!sure) return;
    finish(run, () => {});
    await run.ctx.game.abort();
    run.on.left();
  }

  /* ctx: game (api.js), sound, timers, page, terminal ({attach(host), detach(), type(text)}),
     theme (RepoMap's), panelWords (LivePanel's titles), playMap and places (LivePanel's play and
     places), share (TimeShare, for a playground level's figure), storage (like localStorage,
     where the folded choice is kept; blocked or absent is fine). options: level (LevelView),
     active (ActiveView), onSolved(CheckResult), onEnded() when the level stopped being in
     progress elsewhere, onLeft() after the player left. */
  function create(ctx, { level, active, onSolved, onEnded, onLeft }) {
    const playground = ctx.share ? PlaygroundPanel.create({ share: ctx.share, onPress: (person, id) => pressButton(run, person, id), onType: ctx.terminal.type }) : null;
    const live = LivePanel.create({ theme: ctx.theme, words: ctx.panelWords, play: ctx.playMap, places: ctx.places, playground, onChange: ({ newCommits }) => newCommits > 0 && ctx.sound.play("commit") });
    const storage = "storage" in ctx ? ctx.storage : browserStorage();
    const run = { ctx, level, live, playground, storage, folded: false, cardKicker: null, presses: 0, pressing: false, state: { ...active, finished: false }, quest: null, challenge: null, poller: null, on: { solved: onSolved, ended: onEnded, left: onLeft } };
    run.ui = layout(level, live, () => leave(run), () => fold(run, true));
    showPhase(run);
    if (readFolded(storage)) fold(run, true, { save: false, focus: false });
    ctx.terminal.attach(run.ui.terminalHost);
    run.poller = Polling.start({ tick: () => tick(run), timers: ctx.timers, page: ctx.page });

    return {
      element: run.ui.element,

      dispose() {
        run.state.finished = true;
        run.poller.stop();
        ctx.terminal.detach();
      },
    };
  }

  return { create, ADVANCE_MS, FLASH_MS, FOLD_KEY };
})();
