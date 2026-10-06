"use strict";

/*
 * The guided quest's steps (firstcommit/game.py's StepView): done steps fold away, the current
 * one is open, later ones stay hidden until reached. Below them the player can check the whole
 * level at any time. It only shows steps and hands the player's actions to its owner; the
 * server decides whether a step passed. Needs dom.js and markup.js. Defines one global, Quest.
 */

/* global Dom, Markup */
/* exported Quest */

const Quest = (function () {
  const { el } = Dom;

  function commandLine(command, onType) {
    return el("div", { class: "command" },
      el("code", {}, command),
      el("button", { type: "button", class: "btn btn-ghost btn-small type-command", title: "Types the command at the prompt; press Enter in the terminal to run it", onclick: () => onType(command) }, "Type it in the terminal"),
    );
  }

  function answerForm(step, onAnswer, say) {
    const questionId = `question-${step.id}`;
    const input = el("input", { type: "text", "aria-labelledby": questionId, autocomplete: "off", spellcheck: "false", placeholder: step.placeholder || null });
    return el("form", {
      class: "answer",
      onsubmit: (event) => {
        event.preventDefault();
        const answer = input.value.trim();
        if (answer) onAnswer(answer);
        else say("Type your answer in the box first.");
      },
    },
    el("div", { class: "question", id: questionId }, Markup.render(step.question)),
    el("div", { class: "answer-row" }, input, el("button", { type: "submit", class: "btn btn-primary" }, "Check")),
    );
  }

  /* options: steps, step (the current index; steps.length when the quest is done), onAnswer(text),
     onContinue(), onType(command), onCheck() to check the whole level now. */
  function create({ steps, step, onAnswer, onContinue, onType, onCheck }) {
    const count = el("p", { class: "kicker quest-count" });
    const list = el("ol", { class: "quest" });
    const checkButton = el("button", { type: "button", class: "btn btn-ghost btn-small", onclick: () => onCheck() }, "Check my work");
    const checkLine = el("div", { class: "check-feedback", "aria-live": "polite" });
    const element = el("section", { class: "quest-panel", "aria-label": "Guided quest" }, count, list,
      el("div", { class: "quest-check" }, el("p", { class: "muted" }, "Ahead of the steps? The game can check the whole level now."), checkButton, checkLine),
    );
    let feedbackLine = null;
    let shownNote = null;
    let current = step;

    function say(text, kind = "is-note") {
      shownNote = null;
      feedbackLine.className = `step-feedback ${kind}`;
      feedbackLine.replaceChildren(el("p", {}, text));
    }

    function currentStep(item, index) {
      feedbackLine = el("div", { class: "step-feedback", "aria-live": "polite" });
      shownNote = null;
      const actions = {
        answer: () => answerForm(item, onAnswer, say),
        watch: () => el("p", { class: "step-watch" }, el("i", { class: "spinner", "aria-hidden": "true" }), "Waiting for your repository to show it…"),
        read: () => el("button", { type: "button", class: "btn btn-primary step-continue", onclick: () => onContinue() }, "Continue"),
      };
      return el("li", { class: "step is-current" },
        el("h3", { tabindex: "-1" }, `Step ${index + 1}`),
        el("div", { class: "prose" }, Markup.render(item.text)),
        item.command && commandLine(item.command, onType),
        actions[item.kind](),
        feedbackLine,
      );
    }

    function stepItem(item, index) {
      if (index > current) return el("li", { class: "step is-later" }, el("h3", {}, `Step ${index + 1}`));
      if (index === current) return currentStep(item, index);
      return el("li", { class: "step is-done" },
        el("details", {}, el("summary", {}, el("span", { class: "check", "aria-hidden": "true" }, "✓"), `Step ${index + 1}: `, Markup.plain(item.text).split("\n")[0]), el("div", { class: "prose" }, Markup.render(item.text))),
      );
    }

    function draw() {
      count.textContent = current < steps.length ? `Guided quest · Step ${current + 1} of ${steps.length}` : "Guided quest · done";
      list.replaceChildren(...steps.map(stepItem));
    }

    draw();

    return {
      element,

      setStep(index) {
        current = index;
        draw();
        const heading = list.querySelector(".step.is-current h3");
        if (heading) heading.focus();
      },

      /* The server's verdict on the current step. */
      feedback(blocks, correct) {
        shownNote = null;
        feedbackLine.className = `step-feedback ${correct ? "is-correct" : "is-wrong"}`;
        feedbackLine.replaceChildren(...Markup.render(blocks));
      },

      /* What a watch step says while it has not passed. The same text is left in place, so the
         live region does not announce it again on every poll. */
      note(blocks) {
        const text = JSON.stringify(blocks);
        if (text === shownNote) return;
        shownNote = text;
        feedbackLine.className = "step-feedback is-note";
        feedbackLine.replaceChildren(...Markup.render(blocks));
      },

      /* The result of checking the whole level by hand. */
      checkFeedback(blocks, solved) {
        checkLine.className = `check-feedback ${solved ? "is-correct" : "is-wrong"}`;
        checkLine.replaceChildren(...Markup.render(blocks));
      },

      busy(on) {
        for (const control of list.querySelectorAll(".step.is-current button")) control.disabled = on;
        checkButton.disabled = on;
      },
    };
  }

  return { create };
})();
