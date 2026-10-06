"use strict";

/*
 * Playing a level: the guided quest, then the challenge, beside the live panel and the
 * terminal. It keeps no game state of its own: the step, the hints and whether the level is
 * solved come from the server's replies, and the page polls the lab while the player works
 * (poll.js). Expected failures are handled here, by HTTP status: 409 means the level is no
 * longer in progress (solved or ended from the command line or another tab), 0 means the server
 * did not answer. Anything else is a bug and is left to surface. Needs dom.js, markup.js,
 * map.js, poll.js, dialog.js, live.js, quest.js and challenge.js. Defines one global, Practice.
 */

/* global Dom, Dialog, LivePanel, Polling, Quest, Challenge */
/* exported Practice */

const Practice = (function () {
  const { el } = Dom;
  const ADVANCE_MS = 1100;

  function layout(level, live, onLeave) {
    const parts = {
      body: el("div", { class: "practice-body" }),
      offline: el("p", { class: "banner is-warning offline", role: "status", hidden: true }, "The game server is not answering. Is it still running in your terminal?"),
    };
    /* The terminal docks at the bottom of this column: termlab sizes it against its parent. */
    parts.terminalHost = el("section", { class: "practice-main", "aria-label": "Your repository and terminal" }, el("div", { class: "practice-live" }, live.element));
    parts.element = el("div", { class: "practice" },
      el("aside", { class: "practice-side", "aria-label": "Level" },
        el("header", { class: "practice-head" },
          el("p", { class: "kicker" }, level.chapter_title),
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
     last told it, plus `finished`), the quest or challenge on screen, the poller and the owner's
     callbacks. */

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
      });
      ui.body.replaceChildren(run.quest.element);
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
  }

  /* A quest step's result; a watch step polled without the player is silent until it passes. */
  function stepped(run, result, watched = false) {
    const { quest, state, ctx } = run;
    if (!result.correct && !watched) {
      quest.feedback(result.message, false);
      ctx.sound.play("wrong");
    }
    if (!result.correct) return;
    state.step = result.step;
    quest.feedback(result.message, true);
    ctx.sound.play(watched ? "step" : "correct");
    ctx.timers.setTimeout(() => {
      if (state.finished) return;
      if (state.step < state.steps && run.quest) run.quest.setStep(state.step);
      else showPhase(run);
    }, ADVANCE_MS);
  }

  function checked(run, result) {
    if (result.solved) {
      finish(run, () => run.on.solved(result));
    } else if (run.challenge) {
      run.challenge.feedback(result.message, false);
      run.ctx.sound.play("wrong");
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
      run.live.update(await game.observe());
      run.ui.offline.hidden = true;
      if (plan.watchStep) stepped(run, await game.step(null), true);
      if (plan.autoCheck && !run.state.finished) checked(run, await game.check(null, true));
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
     theme (RepoMap's). options: level (LevelView), active (ActiveView), onSolved(CheckResult),
     onEnded() when the level stopped being in progress elsewhere, onLeft() after the player left. */
  function create(ctx, { level, active, onSolved, onEnded, onLeft }) {
    const live = LivePanel.create({ theme: ctx.theme, onChange: ({ newCommits }) => newCommits > 0 && ctx.sound.play("commit") });
    const run = { ctx, level, live, state: { ...active, finished: false }, quest: null, challenge: null, poller: null, on: { solved: onSolved, ended: onEnded, left: onLeft } };
    run.ui = layout(level, live, () => leave(run));
    showPhase(run);
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

  return { create, ADVANCE_MS };
})();
