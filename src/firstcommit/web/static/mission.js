"use strict";

/*
 * The mission panel beside the terminal: the level's brief, its goals in order (the quest's
 * steps, done ones checked, the current one marked), and the hints. A goal the game watches for
 * passes from the terminal; one to read has a Continue button; one with a question has its answer
 * box while it is current; a prediction offers its choices as buttons, and any of them passes. A level that asks a question after its steps adds it as the last goal.
 * Any command in the panel types itself in the terminal when clicked. A challenge shows its goals
 * as end states to reach in any order: no goal is current, and nothing types itself. It only shows the level and
 * hands the player's actions to its owner; the server judges everything. Needs dom.js, strings.js, markup.js
 * and art-sprites.js. Defines one global, Mission.
 */

/* global Dom, Strings, Markup, ArtSprites */
/* exported Mission */

const Mission = (function () {
  const { el } = Dom;
  const { t } = Strings;

  function answerForm(question, placeholder, onSend, label) {
    const input = el("input", { type: "text", autocomplete: "off", spellcheck: "false", "aria-label": t("mission.answer"), placeholder: placeholder || null });
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
      read: () => el("div", { class: "goal-act" }, el("button", { type: "button", class: "btn btn-primary btn-small goal-continue", onclick: () => on.onContinue() }, t("mission.continue"))),
      answer: () => answerForm(step.question, step.placeholder, on.onAnswer, t("mission.reply")),
      choice: () => el("div", { class: "goal-choices" },
        el("div", { class: "goal-question" }, Markup.render(step.question)),
        el("div", { class: "goal-act" }, step.choices.map((choice) => el("button", { type: "button", class: "btn goal-choice", onclick: () => on.onChoose(choice.value) }, Markup.spans(choice.text.flatMap((block) => block.spans || []))))),
      ),
      watch: () => null,
    };
    return actions[step.kind]();
  }

  function goal(blocks, state, action) {
    return el("li", { class: state ? `goal is-${state}` : "goal" },
      el("span", { class: "goal-box", "aria-hidden": "true" }),
      el("div", { class: "goal-text" }, Markup.render(blocks), state === "done" && el("span", { class: "sr-only" }, t("mission.done")), action),
    );
  }

  const stateOf = (index, current) => (index < current ? "done" : index === current ? "current" : null);

  /* A guided quest's goals are met in order, so the first `current` are done; a challenge's goals
     are met in any order, so each is done when its id is in `done`, and none is current. */
  function goals(level, current, done, on) {
    const state = (step, index) => (level.challenge ? (done.includes(step.id) ? "done" : null) : stateOf(index, current));
    const steps = level.steps.map((step, index) => goal(step.text, state(step, index), !level.challenge && index === current && currentAction(step, on)));
    const asks = level.question.length > 0;
    const last = asks && goal(level.question, stateOf(level.steps.length, current), current === level.steps.length && answerForm([], level.placeholder, on.onCheck, t("mission.check")));
    return [steps, last];
  }

  /* A command as typed at the prompt: an example's "$ " is not part of it. */
  const command = (text) => text.replace(/^\$\s+/, "");

  /* options: level (LevelView), active (ActiveView), onAnswer(text), onContinue(), onChoose(value),
     onCheck(answer), onHint(), onType(command). */
  function create({ level, active, ...on }) {
    let current = active.step;
    let done = active.done;
    let used = active.hints;
    const total = active.hints_total;
    const list = el("ol", { class: "goals" });
    const hintList = el("div", { class: "hint-list" }, level.hints.map((blocks) => el("div", {}, Markup.render(blocks))));
    const hintButton = el("button", { type: "button", class: "btn", onclick: () => on.onHint() }, ArtSprites.icon("hint"), t("mission.askHint"));
    const hintNote = el("small", {});
    let cost = null;
    const element = el("aside", { class: "mission px", "aria-label": t("mission.label") },
      el("div", { class: "brief" }, Markup.render(level.briefing)),
      el("h3", {}, t(level.challenge ? "mission.endState" : "mission.goals")),
      list,
      hintList,
      el("div", { class: "hint-row" }, hintButton, hintNote),
      !level.challenge && el("p", { class: "tapnote" }, t("mission.tap")),
    );
    element.addEventListener("click", (event) => {
      const code = event.target.closest && event.target.closest("code");
      if (code && !level.challenge && !event.target.closest("button")) on.onType(command(code.textContent));
    });

    function drawGoals() {
      list.replaceChildren(...goals(level, current, done, on).flat().filter(Boolean));
    }

    function drawHints() {
      hintButton.disabled = used >= total;
      let price = t("mission.hintCost");
      if (cost !== null) price = cost ? t("mission.hintPaid", { cost }) : t("mission.hintFree");
      hintNote.textContent = `${price} ${used < total ? t("mission.hintsLeft", { count: total - used }) : t("mission.noHints")}`;
    }

    drawGoals();
    drawHints();

    return {
      element,

      /* The quest's place: the step it is at, and the ids of the goals met (StepResult.done). */
      setStep(step, met = done) {
        current = step;
        done = met;
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
        done = level.steps.map((step) => step.id);
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
