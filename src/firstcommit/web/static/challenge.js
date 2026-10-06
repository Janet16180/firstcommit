"use strict";

/*
 * The level's challenge: its briefing, an answer box for levels that ask a question, a button
 * to check now (the page also checks by itself while the player works), and hints, each
 * costing a little XP. The server judges everything. Needs dom.js and markup.js. Defines one
 * global, Challenge.
 */

/* global Dom, Markup */
/* exported Challenge */

const Challenge = (function () {
  const { el } = Dom;

  /* options: level (LevelView), active (ActiveView), onCheck(answer or null), onHint(). */
  function create({ level, active, onCheck, onHint }) {
    let used = active.hints;
    const total = active.hints_total;
    const input = el("input", { type: "text", id: "challenge-answer", autocomplete: "off", spellcheck: "false" });
    const checkButton = el("button", { type: "submit", class: "btn btn-primary" }, "Check my work");
    const feedbackLine = el("div", { class: "check-feedback", "aria-live": "polite" });
    const hintButton = el("button", { type: "button", class: "btn btn-ghost btn-small hint-button", onclick: () => onHint() });
    const usedLine = el("p", { class: "hints-used muted" });
    const hintList = el("ol", { class: "hints" });
    const element = el("section", { class: "challenge", "aria-label": "Challenge" },
      el("p", { class: "kicker" }, "The challenge"),
      el("div", { class: "briefing prose" }, Markup.render(level.briefing)),
      el("p", { class: "auto-check muted" }, el("i", { class: "pulse", "aria-hidden": "true" }), "The game checks your repository as you work."),
      el("form", {
        class: "answer",
        onsubmit: (event) => {
          event.preventDefault();
          onCheck(input.value.trim() || null);
        },
      },
      el("label", { for: "challenge-answer" }, "Your answer, if the task asks a question"),
      el("div", { class: "answer-row" }, input, checkButton),
      ),
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
        hintList.append(el("li", {}, el("div", { class: "prose" }, Markup.render(hint.hint)), el("p", { class: "hint-cost muted" }, `Hint ${hint.used} of ${hint.total}, cost ${hint.cost} XP`)));
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
