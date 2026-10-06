"use strict";

/*
 * The level's challenge: its briefing, an answer box when the level asks a question, a button
 * to check now (the page also checks by itself while the player works), and hints, each
 * costing a little XP, with the ones already revealed in this play. The server judges everything. Needs dom.js and markup.js. Defines one
 * global, Challenge.
 */

/* global Dom, Markup */
/* exported Challenge */

const Challenge = (function () {
  const { el } = Dom;

  function hintItem(blocks, number, total, cost) {
    return el("li", {}, el("div", { class: "prose" }, Markup.render(blocks)), el("p", { class: "hint-cost muted" }, `Hint ${number} of ${total}${cost === null ? "" : `, cost ${cost} XP`}`));
  }

  /* The answer form: a box for the level's question when it asks one, else only the button. */
  function checkForm(level, checkButton, onCheck) {
    const input = level.question && el("input", { type: "text", id: "challenge-answer", autocomplete: "off", spellcheck: "false", placeholder: level.placeholder || null });
    return el("form", {
      class: "answer",
      onsubmit: (event) => {
        event.preventDefault();
        onCheck(input ? input.value.trim() || null : null);
      },
    },
    input && el("label", { for: "challenge-answer" }, level.question),
    el("div", { class: "answer-row" }, input, checkButton),
    );
  }

  /* options: level (LevelView), active (ActiveView), onCheck(answer or null), onHint(). */
  function create({ level, active, onCheck, onHint }) {
    let used = active.hints;
    const total = active.hints_total;
    const checkButton = el("button", { type: "submit", class: "btn btn-primary" }, "Check my work");
    const feedbackLine = el("div", { class: "check-feedback", "aria-live": "polite" });
    const hintButton = el("button", { type: "button", class: "btn btn-ghost btn-small hint-button", onclick: () => onHint() });
    const usedLine = el("p", { class: "hints-used muted" });
    const hintList = el("ol", { class: "hints" }, level.hints.map((blocks, index) => hintItem(blocks, index + 1, total, null)));
    const element = el("section", { class: "challenge", "aria-label": "Challenge" },
      el("p", { class: "kicker", tabindex: "-1" }, "The challenge"),
      el("div", { class: "briefing prose" }, Markup.render(level.briefing)),
      el("p", { class: "auto-check muted" }, el("i", { class: "pulse", "aria-hidden": "true" }), "The game checks your repository as you work."),
      checkForm(level, checkButton, onCheck),
      feedbackLine,
      el("div", { class: "hint-box" }, hintButton, usedLine, hintList),
    );

    function drawHints() {
      hintButton.textContent = used < total ? `Show a hint (${total - used} left)` : "No hints left";
      hintButton.disabled = used >= total;
      usedLine.textContent = total ? `Hints used: ${used} of ${total}. Each one costs a little XP.` : "This level has no hints.";
    }

    drawHints();

    return {
      element,

      feedback(blocks, solved) {
        feedbackLine.className = `check-feedback ${solved ? "is-correct" : "is-wrong"}`;
        feedbackLine.replaceChildren(...Markup.render(blocks));
      },

      /* A hint the server revealed (HintView). */
      addHint(hint) {
        used = hint.used;
        hintList.append(hintItem(hint.hint, hint.used, hint.total, hint.cost));
        drawHints();
      },

      busy(on) {
        checkButton.disabled = on;
        hintButton.disabled = on || used >= total;
      },
    };
  }

  return { create };
})();
