"use strict";

/*
 * The mission panel beside the terminal: the level's brief, its goals in order (the quest's
 * steps, done ones checked, the current one marked), and the hints. A goal the game watches for
 * passes from the terminal; one to read has a Continue button; one with a question has its answer
 * box while it is current. A level that asks a question after its steps adds it as the last goal.
 * Any command in the panel types itself in the terminal when clicked. It only shows the level and
 * hands the player's actions to its owner; the server judges everything. Needs dom.js, markup.js
 * and art-sprites.js. Defines one global, Mission.
 */

/* global Dom, Markup, ArtSprites */
/* exported Mission */

const Mission = (function () {
  const { el } = Dom;

  function answerForm(question, placeholder, onSend, label) {
    const input = el("input", { type: "text", autocomplete: "off", spellcheck: "false", "aria-label": "Your answer", placeholder: placeholder || null });
    return el("form", {
      class: "goal-answer",
      onsubmit: (event) => {
        event.preventDefault();
        const answer = input.value.trim();
        if (answer) onSend(answer);
      },
    },
    el("div", { class: "goal-question" }, Markup.render(question)),
    el("div", { class: "goal-act" }, input, el("button", { type: "submit", class: "btn btn-primary btn-small" }, label)),
    );
  }

  /* What the current goal offers besides its text. */
  function currentAction(step, on) {
    const actions = {
      read: () => el("div", { class: "goal-act" }, el("button", { type: "button", class: "btn btn-primary btn-small goal-continue", onclick: () => on.onContinue() }, "Continue")),
      answer: () => answerForm(step.question, step.placeholder, on.onAnswer, "Answer"),
      watch: () => null,
    };
    return actions[step.kind]();
  }

  function goal(blocks, state, action) {
    return el("li", { class: state ? `goal is-${state}` : "goal" },
      el("span", { class: "goal-box", "aria-hidden": "true" }),
      el("div", { class: "goal-text" }, Markup.render(blocks), state === "done" && el("span", { class: "sr-only" }, " (done)"), action),
    );
  }

  const stateOf = (index, current) => (index < current ? "done" : index === current ? "current" : null);

  function goals(level, current, on) {
    const steps = level.steps.map((step, index) => goal(step.text, stateOf(index, current), index === current && currentAction(step, on)));
    const asks = level.question.length > 0;
    const last = asks && goal(level.question, stateOf(level.steps.length, current), current === level.steps.length && answerForm([], level.placeholder, on.onCheck, "Check"));
    return [steps, last];
  }

  /* A command as typed at the prompt: an example's "$ " is not part of it. */
  const command = (text) => text.replace(/^\$\s+/, "");

  /* options: level (LevelView), active (ActiveView), onAnswer(text), onContinue(), onCheck(answer),
     onHint(), onType(command). */
  function create({ level, active, ...on }) {
    let current = active.step;
    let used = active.hints;
    const total = active.hints_total;
    const list = el("ol", { class: "goals" });
    const hintList = el("div", { class: "hint-list" }, level.hints.map((blocks) => el("div", {}, Markup.render(blocks))));
    const hintButton = el("button", { type: "button", class: "btn", onclick: () => on.onHint() }, ArtSprites.icon("hint"), "Ask for a hint");
    const hintNote = el("small", {});
    let cost = null;
    const element = el("aside", { class: "mission px", "aria-label": "Mission" },
      el("div", { class: "brief" }, Markup.render(level.briefing)),
      el("h3", {}, "Goals"),
      list,
      hintList,
      el("div", { class: "hint-row" }, hintButton, hintNote),
      el("p", { class: "tapnote" }, "Click any highlighted command to type it in the terminal."),
    );
    element.addEventListener("click", (event) => {
      const code = event.target.closest && event.target.closest("code");
      if (code) on.onType(command(code.textContent));
    });

    function drawGoals() {
      list.replaceChildren(...goals(level, current, on).flat().filter(Boolean));
    }

    function drawHints() {
      hintButton.disabled = used >= total;
      const price = cost === null ? "A hint costs a star and this play's XP." : `That hint cost ${cost ? `${cost} XP` : "no XP"}.`;
      hintNote.textContent = `${price} ${used < total ? `${total - used} left.` : "No hints left."}`;
    }

    drawGoals();
    drawHints();

    return {
      element,

      setStep(step) {
        current = step;
        drawGoals();
      },

      /* What the game says about the current goal while it waits for it, under that goal. The same
         text is left in place, so it is not announced again on every poll. */
      note(blocks) {
        const text = list.querySelector(".goal.is-current .goal-text");
        if (!text) return;
        const shown = text.querySelector(".goal-note");
        if (shown && shown.dataset.text === JSON.stringify(blocks)) return;
        const note = el("div", { class: "goal-note", "aria-live": "polite", "data-text": JSON.stringify(blocks) }, Markup.render(blocks));
        if (shown) shown.replaceWith(note);
        else text.append(note);
      },

      /* Every goal checked: the level is solved. */
      solved() {
        current = Infinity;
        drawGoals();
      },

      /* A hint the server revealed (HintView). */
      addHint(hint) {
        used = hint.used;
        cost = hint.cost;
        hintList.append(el("div", {}, Markup.render(hint.hint)));
        drawHints();
      },

      busy(waiting) {
        for (const control of list.querySelectorAll(".goal.is-current button")) control.disabled = waiting;
        hintButton.disabled = waiting || used >= total;
      },
    };
  }

  return { create };
})();
