"use strict";

/*
 * Flashcards (firstcommit/game.py's CardView and CardResult): a round of up to ten cards,
 * due ones first, as the server picks them. Choices are numbered (keys 1 to 9 pick them);
 * the server judges each reply, schedules the card and pays XP. Needs dom.js and markup.js.
 * Defines one global, CardsView.
 */

/* global Dom, Markup */
/* exported CardsView */

const CardsView = (function () {
  const { el } = Dom;
  const ROUND = 10;
  const LEVELS = { 1: "basic", 2: "deeper", 3: "advanced" };

  /* Everything below works on one `round`: ctx, chapter, the cards, the index of the one on
     show, its results so far, the element and whether the current card is answered. */

  function chapterTitle(round) {
    const chapter = round.ctx.status().chapters.find((item) => item.id === round.chapter);
    return chapter ? chapter.title : "All chapters";
  }

  function enable(round, on) {
    for (const button of round.element.querySelectorAll("button.choice, form button")) button.disabled = !on;
  }

  async function reply(round, text, chosen) {
    if (round.answered) return;
    round.answered = true;
    const card = round.cards[round.index];
    enable(round, false);
    let result = null;
    try {
      result = await round.ctx.game.card(card.id, text);
    } catch (error) {
      if (error.status !== 0) throw error;
      round.answered = false;
      enable(round, true);
      round.element.querySelector(".card-result").replaceChildren(el("p", { class: "notice" }, "The game server did not answer. Is it still running? Try again."));
      return;
    }
    round.results.push(result);
    round.ctx.sound.play(result.correct ? "correct" : "wrong");
    for (const button of round.element.querySelectorAll("button.choice")) {
      button.classList.toggle("is-right", button.dataset.choice === result.answer);
      button.classList.toggle("is-wrong", button === chosen && !result.correct);
    }
    showResult(round, result);
    round.ctx.refresh();
  }

  function showResult(round, result) {
    const nextButton = el("button", { type: "button", class: "btn btn-primary card-next", onclick: () => advance(round) }, round.index + 1 < round.cards.length ? "Next card" : "Finish");
    round.element.querySelector(".card-result").replaceChildren(
      el("p", { class: result.correct ? "verdict is-correct" : "verdict is-wrong" }, result.correct ? "Right." : "Not this time. The answer: ", !result.correct && el("strong", {}, result.answer)),
      el("div", { class: "prose" }, Markup.render(result.explain)),
      el("p", { class: "card-score" },
        result.xp > 0 && el("span", { class: "xp" }, `+${result.xp} XP`),
        result.bonus > 0 && el("span", { class: "xp" }, `+${result.bonus} streak bonus`),
        el("span", {}, `Streak: ${result.streak}`),
      ),
      nextButton,
    );
    nextButton.focus();
  }

  function cardView(round) {
    const card = round.cards[round.index];
    const input = el("input", { type: "text", autocomplete: "off", spellcheck: "false", placeholder: card.placeholder || null, "aria-label": "Your answer" });
    const choices = el("ol", { class: "choices" }, card.choices.map((choice, index) => el("li", {},
      el("button", { type: "button", class: "choice", "data-choice": choice, onclick: (event) => reply(round, choice, event.currentTarget) }, el("kbd", {}, String(index + 1)), choice),
    )));
    const form = el("form", {
      class: "answer",
      onsubmit: (event) => {
        event.preventDefault();
        if (input.value.trim()) reply(round, input.value.trim(), null);
      },
    }, el("div", { class: "answer-row" }, input, el("button", { type: "submit", class: "btn btn-primary" }, "Check")));
    return el("section", { class: "cards panel narrow", "aria-live": "polite" },
      el("p", { class: "kicker card-count" }, `Card ${round.index + 1} of ${round.cards.length} · ${chapterTitle(round)}`),
      el("p", { class: "card-level" }, LEVELS[card.level] || ""),
      !card.pays && el("p", { class: "card-pays muted" }, "Practice only: no XP, this card is not due yet."),
      el("div", { class: "card-prompt prose" }, Markup.render(card.prompt)),
      card.code && el("pre", { class: "code card-code" }, el("code", {}, card.code)),
      card.choices.length ? choices : form,
      el("div", { class: "card-result" }),
    );
  }

  function summary(round) {
    const right = round.results.filter((result) => result.correct).length;
    const xp = round.results.reduce((sum, result) => sum + result.xp + result.bonus, 0);
    return el("section", { class: "cards-summary panel narrow" },
      el("p", { class: "kicker" }, "Round complete"),
      el("h1", {}, `${right} of ${round.results.length} right`),
      el("p", {}, xp > 0 ? `+${xp} XP this round.` : "No XP this round: these cards were not due yet."),
      el("div", { class: "actions" },
        el("button", { type: "button", class: "btn btn-primary", onclick: () => start(round) }, "Another round"),
        el("a", { class: "btn btn-quiet", href: "#/" }, "Back to the map"),
      ),
    );
  }

  function advance(round) {
    round.index += 1;
    round.answered = false;
    const next = round.index < round.cards.length ? cardView(round) : summary(round);
    round.element.replaceChildren(next);
    if (round.index < round.cards.length) round.ctx.sound.play("card");
  }

  async function start(round) {
    round.cards = await round.ctx.game.cards(round.chapter, ROUND);
    round.index = -1;
    round.results = [];
    if (!round.cards.length) {
      round.element.replaceChildren(el("section", { class: "panel narrow" }, el("h1", {}, "No cards to review"), el("p", {}, "Every card is scheduled for later. Come back tomorrow, or play a level."), el("a", { class: "btn btn-primary", href: "#/" }, "Back to the map")));
      return;
    }
    advance(round);
  }

  /* ctx: game, status(), refresh(), sound. `chapter` is a chapter id, or null for every chapter. */
  function create(ctx, chapter) {
    const round = { ctx, chapter, cards: [], index: -1, results: [], answered: false, element: el("div", { class: "cards-page" }, el("p", { class: "loading" }, "Picking your cards…")) };
    start(round);
    return {
      element: round.element,

      keydown(event) {
        const choice = round.element.querySelectorAll("button.choice")[Number(event.key) - 1];
        if (!choice || round.answered || event.target.closest("input, textarea") || event.altKey || event.ctrlKey || event.metaKey) return;
        event.preventDefault();
        choice.click();
      },
    };
  }

  return { create };
})();
