"use strict";

/*
 * The map of chapters: the player's rank and XP, the level to play next, the cards due, and
 * every chapter with its levels in play order (from firstcommit/game.py's Status). Needs
 * dom.js, progress.js and dialog.js. Defines one global, HomeView.
 */

/* global Dom, Progress, Dialog */
/* exported HomeView */

const HomeView = (function () {
  const { el } = Dom;
  const plural = (count, word) => `${count} ${word}${count === 1 ? "" : "s"}`;
  const levelHref = (id) => `#/level/${encodeURIComponent(id)}`;

  function rankBlock(status) {
    const { rank, xp } = status;
    const { fraction, toNext } = Progress.rankProgress(status);
    const percent = Math.round(fraction * 100);
    return el("div", { class: "hero-rank" },
      el("p", { class: "kicker" }, "Your rank"),
      el("h1", {}, rank.title),
      el("div", { class: "meter", role: "progressbar", "aria-label": "Progress to the next rank", "aria-valuemin": "0", "aria-valuemax": "100", "aria-valuenow": String(percent) }, el("i", { style: `width: ${percent}%` })),
      el("p", { class: "muted" }, toNext === null ? `${xp} XP · the top rank` : `${xp} XP · ${toNext} XP to ${rank.next_title}`),
    );
  }

  function playBlock(status) {
    const { active } = status;
    const activeLevel = active && Progress.findLevel(status.chapters, active.level);
    if (activeLevel) {
      const quest = active.step < active.steps ? `Guided quest, step ${active.step + 1} of ${active.steps}` : "The challenge is waiting";
      return [el("a", { class: "btn btn-primary btn-large", href: levelHref(active.level) }, `Continue: ${activeLevel.title}`), el("p", { class: "muted" }, quest)];
    }
    const next = Progress.nextLevel(status.chapters);
    const started = status.chapters.some((chapter) => chapter.levels.some((level) => level.done));
    if (!next) return el("p", {}, "You have played every level. Well done.");
    return el("a", { class: "btn btn-primary btn-large", href: levelHref(next.id) }, `${started ? "Next" : "Start here"}: ${next.title}`);
  }

  function hero(status) {
    return el("section", { class: "hero panel" },
      rankBlock(status),
      el("div", { class: "hero-actions" },
        playBlock(status),
        status.cards_due > 0 && el("a", { class: "btn btn-ghost", href: "#/cards" }, `Review ${plural(status.cards_due, "card")}`),
      ),
    );
  }

  function levelLink(level, status) {
    const active = status.active && status.active.level === level.id;
    const classes = ["level-link", level.done && "is-done", active && "is-active"].filter(Boolean).join(" ");
    return el("li", {}, el("a", { class: classes, href: levelHref(level.id) },
      el("span", { class: "level-state", "aria-hidden": "true" }, level.done ? "✓" : active ? "▸" : ""),
      el("span", { class: "level-title" }, level.title, level.done && el("span", { class: "sr-only" }, " (done)"), active && el("span", { class: "sr-only" }, " (in progress)")),
      el("span", { class: "level-meta" }, `${"●".repeat(level.difficulty)}${"○".repeat(status.max_difficulty - level.difficulty)}`, ` · ${level.xp} XP`),
    ));
  }

  function chapterItem(chapter, index, status) {
    const done = chapter.levels.filter((level) => level.done).length;
    const id = encodeURIComponent(chapter.id);
    return el("li", { class: `chapter${chapter.levels.length ? "" : " is-empty"}` },
      el("header", { class: "chapter-head" },
        el("span", { class: "chapter-number", "aria-hidden": "true" }, String(index + 1)),
        el("div", {}, el("h2", {}, chapter.title), el("p", { class: "muted" }, chapter.levels.length ? `${done} of ${plural(chapter.levels.length, "level")} done` : "Coming soon")),
      ),
      chapter.levels.length > 0 && el("ul", { class: "levels" }, chapter.levels.map((level) => levelLink(level, status))),
      chapter.cards > 0 && el("p", { class: "chapter-links" }, el("a", { href: `#/notes/${id}` }, "Notes"), el("a", { href: `#/cards/${id}` }, `Practise ${plural(chapter.cards, "card")}`)),
    );
  }

  async function erase(ctx) {
    const sure = await Dialog.confirm({
      title: "Erase all progress?",
      text: "Your XP, finished levels and card schedule are deleted, and any level in progress ends. This cannot be undone.",
      confirm: "Erase everything",
      cancel: "Keep my progress",
      danger: true,
    });
    if (!sure) return;
    await ctx.game.reset();
    await ctx.refresh();
    ctx.reload();
  }

  /* ctx: status(), game, refresh(), reload() (shows this view again). */
  function create(ctx) {
    const status = ctx.status();
    const element = el("div", { class: "home" },
      hero(status),
      el("ol", { class: "chapters" }, status.chapters.map((chapter, index) => chapterItem(chapter, index, status))),
      el("footer", { class: "home-foot" }, el("button", { type: "button", class: "link-button is-danger erase", onclick: () => erase(ctx) }, "Erase all progress…")),
    );
    return { element };
  }

  return { create };
})();
