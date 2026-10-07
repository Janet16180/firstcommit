"use strict";

/*
 * Flashcards (firstcommit/game.py's CardView and CardResult): a round of up to ten cards,
 * due ones first, as the server picks them. Choices are numbered (keys 1 to 9 pick them); each
 * shows its text and sends its raw value back. The server judges each reply, schedules the
 * card and pays XP. Needs dom.js, strings.js and markup.js.
 * Defines one global, CardsView.
 */

/* global Dom, Strings, Markup */
/* exported CardsView */

const CardsView = (function () {
  const { el } = Dom;
  const { t } = Strings;
  const ROUND = 10;

  /* Everything below works on one `round`: ctx, chapter, the cards, the index of the one on
     show, its results so far, the element and whether the current card is answered. */

  function chapterTitle(round) {
    const chapter = round.ctx.status().chapters.find((item) => item.id === round.chapter);
    return chapter ? chapter.title : t("cards.all");
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
      round.element.querySelector(".card-result").replaceChildren(el("p", { class: "notice" }, t("cards.down")));
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
    const nextButton = el("button", { type: "button", class: "btn btn-primary card-next", onclick: () => advance(round) }, round.index + 1 < round.cards.length ? t("cards.next") : t("cards.finish"));
    const verdict = result.correct
      ? el("p", { class: "verdict is-correct" }, t("cards.right"))
      : el("div", { class: "verdict is-wrong" }, el("p", {}, t("cards.wrong")), el("div", { class: "right-answer prose" }, Markup.render(result.answer_text)));
    round.element.querySelector(".card-result").replaceChildren(
      verdict,
      el("div", { class: "prose" }, Markup.render(result.explain)),
      el("p", { class: "card-score" },
        result.xp > 0 && el("span", { class: "xp" }, t("cards.xp", { xp: result.xp })),
        result.bonus > 0 && el("span", { class: "xp" }, t("cards.bonus", { bonus: result.bonus })),
        el("span", {}, t("cards.streak", { streak: result.streak })),
      ),
      nextButton,
    );
    nextButton.focus();
  }

  function cardView(round) {
    const card = round.cards[round.index];
    const input = el("input", { type: "text", autocomplete: "off", spellcheck: "false", placeholder: card.placeholder || null, "aria-label": t("cards.answer") });
    const choices = el("ol", { class: "choices" }, card.choices.map((choice, index) => el("li", {},
      el("button", { type: "button", class: "choice", "data-choice": choice.value, onclick: (event) => reply(round, choice.value, event.currentTarget) },
        el("kbd", {}, String(index + 1)),
        el("span", { class: "choice-text" }, Markup.render(choice.text)),
      ),
    )));
    const form = el("form", {
      class: "answer",
      onsubmit: (event) => {
        event.preventDefault();
        if (input.value.trim()) reply(round, input.value.trim(), null);
      },
    }, el("div", { class: "answer-row" }, input, el("button", { type: "submit", class: "btn btn-primary" }, t("cards.check"))));
    return el("section", { class: "cards panel narrow", "aria-live": "polite" },
      el("p", { class: "kicker card-count" }, t("cards.count", { number: round.index + 1, total: round.cards.length, chapter: chapterTitle(round) })),
      el("p", { class: "card-level" }, card.level_name),
      !card.pays && el("p", { class: "card-pays muted" }, t("cards.practice")),
      el("div", { class: "card-prompt prose" }, Markup.render(card.prompt)),
      card.code && el("pre", { class: "code card-code" }, el("code", {}, card.code)),
      card.choices.length ? choices : form,
      el("div", { class: "card-result" }),
    );
  }

  /* What the round paid, as the server reported it; "not due" only when no card could pay. */
  function roundPay(round) {
    const xp = round.results.reduce((sum, result) => sum + result.xp + result.bonus, 0);
    let line = t("cards.noXp");
    if (xp > 0) line = t("cards.roundXp", { xp });
    else if (!round.cards.some((card) => card.pays)) line = t("cards.notDue");
    return line;
  }

  function summary(round) {
    const right = round.results.filter((result) => result.correct).length;
    return el("section", { class: "cards-summary panel narrow" },
      el("p", { class: "kicker" }, t("cards.complete")),
      el("h1", {}, t("cards.score", { right, total: round.results.length })),
      el("p", {}, roundPay(round)),
      el("div", { class: "actions" },
        el("button", { type: "button", class: "btn btn-primary", onclick: () => start(round) }, t("cards.another")),
        el("a", { class: "btn btn-quiet", href: "#/" }, t("cards.back")),
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
      round.element.replaceChildren(el("section", { class: "panel narrow" }, el("h1", {}, t("cards.none")), el("p", {}, t("cards.later")), el("a", { class: "btn btn-primary", href: "#/" }, t("cards.back"))));
      return;
    }
    advance(round);
  }

  /* ctx: game, status(), refresh(), sound. `chapter` is a chapter id, or null for every chapter. */
  function create(ctx, chapter) {
    const round = { ctx, chapter, cards: [], index: -1, results: [], answered: false, element: el("div", { class: "cards-page" }, el("p", { class: "loading" }, t("cards.picking"))) };
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
