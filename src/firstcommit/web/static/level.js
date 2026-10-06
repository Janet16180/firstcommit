"use strict";

/*
 * A level's page, in phases: its introduction, the lesson (lesson.js), the practice
 * (practice.js), then the celebration and the debrief. Which phase opens comes from the server:
 * a level in progress opens in the practice, any other on its introduction. Nothing here is
 * specific to a level; everything shown comes from the level's records. Needs dom.js,
 * markup.js, progress.js, lesson.js and practice.js. Defines one global, LevelPage.
 */

/* global Dom, Markup, Progress, LessonPlayer, Practice */
/* exported LevelPage */

const LevelPage = (function () {
  const { el } = Dom;
  const SERVER_DOWN = "The game server did not answer. Is it still running in your terminal?";

  const difficulty = (value) => el("span", { class: "difficulty", "aria-label": `difficulty ${value} of 3` },
    [1, 2, 3].map((dot) => el("i", { class: dot <= value ? "is-on" : null, "aria-hidden": "true" })));

  function planSentence(level) {
    const parts = [level.has_lesson && "a short lesson", level.steps.length > 0 && "a guided quest in a real terminal", "a challenge"].filter(Boolean);
    const sentence = parts.length > 1 ? `${parts.slice(0, -1).join(", then ")}, then ${parts[parts.length - 1]}` : parts[0];
    return `${sentence[0].toUpperCase()}${sentence.slice(1)}.`;
  }

  function payoutLine(payout) {
    if (!payout.first_time) return "Played again: no XP this time.";
    const rank = payout.rank_after !== payout.rank_before ? ` · New rank: ${payout.rank_after}` : "";
    return `+${payout.xp} XP${rank}`;
  }

  /* Everything below works on one `page`: ctx, levelId, level (LevelView, once loaded), the
     element and the phase part on show (with dispose and keydown when it has them). */

  function mount(page, node, part = null) {
    if (page.part && page.part.dispose) page.part.dispose();
    page.part = part;
    page.element.replaceChildren(node);
  }

  function missing(page) {
    mount(page, el("section", { class: "panel narrow" }, el("h1", {}, "There is no level here"), el("p", {}, "There is no level with this address. ", el("a", { href: "#/" }, "Back to the map"))));
  }

  /* A failure an action can expect: the level is gone (404) or the server is down (0). */
  function expected(page, error) {
    if (error.status === 404) missing(page);
    if (error.status === 0) intro(page, SERVER_DOWN);
    return error.status === 404 || error.status === 0;
  }

  function introActions(page) {
    const { level } = page;
    const startButton = el("button", { type: "button", class: `btn ${level.has_lesson ? "btn-ghost" : "btn-primary"}`, onclick: () => start(page, startButton) }, level.has_lesson ? "Skip to the practice" : "Start the practice");
    return el("div", { class: "actions" },
      level.has_lesson && el("button", { type: "button", class: "btn btn-primary", onclick: () => lesson(page) }, "Start the lesson"),
      startButton,
      level.debrief && el("button", { type: "button", class: "btn btn-quiet", onclick: () => debrief(page, null, level.debrief) }, "Read the debrief again"),
      el("a", { class: "btn btn-quiet", href: "#/" }, "Back to the map"),
    );
  }

  function intro(page, notice = "") {
    const { level, levelId } = page;
    const status = page.ctx.status();
    const found = Progress.findLevel(status.chapters, levelId);
    const other = status.active && status.active.level !== levelId ? Progress.findLevel(status.chapters, status.active.level) : null;
    mount(page, el("section", { class: "level-intro panel narrow" },
      el("p", { class: "kicker" }, level.chapter_title),
      el("h1", {}, level.title),
      el("ul", { class: "facts" },
        el("li", {}, difficulty(level.difficulty)),
        el("li", {}, `${level.xp} XP`),
        found && found.done && el("li", { class: "is-done" }, "✓ Done"),
      ),
      el("p", { class: "plan" }, planSentence(level)),
      level.steps.length === 0 && el("div", { class: "briefing prose" }, Markup.render(level.briefing)),
      (notice || other) && el("p", { class: "notice", role: "status" }, notice || `Starting this level ends “${other.title}”, which is in progress.`),
      introActions(page),
    ));
  }

  async function lesson(page) {
    const { ctx } = page;
    try {
      const view = await ctx.game.lesson(page.levelId);
      const player = LessonPlayer.create({ lesson: view, theme: ctx.theme, timers: ctx.timers, reducedMotion: ctx.reducedMotion, onFinish: () => start(page, null), onExit: () => intro(page) });
      mount(page, player.element, player);
    } catch (error) {
      if (!expected(page, error)) throw error;
    }
  }

  async function start(page, button) {
    if (button) {
      button.disabled = true;
      button.textContent = "Preparing your practice repository…";
    }
    try {
      const active = await page.ctx.game.start(page.levelId);
      await page.ctx.refresh();
      practice(page, active);
    } catch (error) {
      if (!expected(page, error)) throw error;
    }
  }

  function practice(page, active) {
    const view = Practice.create(page.ctx, {
      level: page.level,
      active,
      onSolved: (result) => won(page, result.payout, result.debrief),
      onEnded: () => endedElsewhere(page),
      onLeft: () => page.ctx.refresh().then(() => intro(page, "You left the level. Its practice repository was deleted.")),
    });
    mount(page, view.element, view);
  }

  /* A win, from the page's own check (with the debrief) or from the terminal (the level's page
     then holds the debrief of its last play). */
  async function won(page, payout, blocks) {
    await page.ctx.refresh();
    await page.ctx.celebrate({ kicker: "Level complete", title: page.level.title, xp: payout.xp, firstTime: payout.first_time, rankBefore: payout.rank_before, rankAfter: payout.rank_after, button: "See what you learned" });
    debrief(page, payout, blocks || (await page.ctx.game.level(page.levelId)).debrief);
  }

  async function endedElsewhere(page) {
    const status = await page.ctx.refresh();
    const payout = status.last_payout;
    if (payout && payout.level === page.levelId) await won(page, payout, null);
    else intro(page, "This level is no longer in progress: it was ended from the command line or in another tab.");
  }

  function debrief(page, payout, blocks) {
    const { level } = page;
    const next = Progress.nextLevel(page.ctx.status().chapters, page.levelId);
    mount(page, el("section", { class: "debrief panel narrow" },
      el("p", { class: "kicker" }, `Debrief · ${level.chapter_title}`),
      el("h1", {}, level.title),
      payout && el("p", { class: "payout" }, payoutLine(payout)),
      blocks ? el("div", { class: "prose" }, Markup.render(blocks)) : el("p", { class: "notice" }, "This level's debrief is not available."),
      el("div", { class: "actions" },
        next && el("a", { class: "btn btn-primary next-level", href: `#/level/${encodeURIComponent(next.id)}` }, `Next: ${next.title}`),
        el("a", { class: `btn ${next ? "btn-ghost" : "btn-primary"}`, href: `#/cards/${encodeURIComponent(level.chapter)}` }, "Review this chapter's cards"),
        el("a", { class: "btn btn-quiet", href: "#/" }, "Back to the map"),
      ),
    ));
  }

  async function load(page) {
    try {
      page.level = await page.ctx.game.level(page.levelId);
    } catch (error) {
      if (error.status !== 404) throw error;
      return missing(page);
    }
    const { active } = page.ctx.status();
    return active && active.level === page.levelId ? practice(page, active) : intro(page);
  }

  /* ctx: game, status(), refresh(), celebrate(options), and what practice.js and the lesson need
     (sound, timers, page, terminal, theme, reducedMotion). */
  function create(ctx, levelId) {
    const page = { ctx, levelId, level: null, part: null, element: el("div", { class: "level-page" }, el("p", { class: "loading" }, "Loading the level…")) };
    load(page);
    return {
      element: page.element,
      keydown: (event) => page.part && page.part.keydown && page.part.keydown(event),
      dispose: () => page.part && page.part.dispose && page.part.dispose(),
    };
  }

  return { create };
})();
