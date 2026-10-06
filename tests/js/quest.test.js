"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { installBrowser, load, record } = require("./load");

const document = installBrowser();
const { Quest } = load(["dom.js", "markup.js", "quest.js"], ["Quest"]);

function quest(step) {
  const seen = { answers: [], continued: 0, typed: [] };
  const made = Quest.create({
    steps: record("level").steps,
    step,
    onAnswer: (answer) => seen.answers.push(answer),
    onContinue: () => (seen.continued += 1),
    onType: (command) => seen.typed.push(command),
  });
  return { ...made, seen, q: (selector) => made.element.querySelector(selector), all: (selector) => made.element.querySelectorAll(selector) };
}

test("done steps fold away, the current step is open, and later steps stay hidden", () => {
  const view = quest(1);
  const items = view.all(".step");
  assert.deepEqual(items.map((item) => item.className), ["step is-done", "step is-current", "step is-later"]);
  assert.match(items[1].textContent, /Ask Git what changed/);
  assert.doesNotMatch(items[2].textContent, /Stage the change/);
  assert.match(items[2].textContent, /Step 3/);
  assert.match(view.q(".quest-count").textContent, /Step 2 of 3/);
});

test("an answer step asks its question and sends the typed answer, trimmed", () => {
  const view = quest(1);
  assert.match(view.q(".step.is-current label").textContent, /Which file has changes/);
  const input = view.q(".step.is-current input");
  assert.equal(input.getAttribute("placeholder"), "a file name");
  input.value = "  notes.txt ";
  view.q(".step.is-current form").dispatchEvent(makeEvent("submit"));
  assert.deepEqual(view.seen.answers, ["notes.txt"]);
});

test("an empty answer is not sent", () => {
  const view = quest(1);
  view.q(".step.is-current form").dispatchEvent(makeEvent("submit"));
  assert.deepEqual(view.seen.answers, []);
  assert.match(view.q(".step-feedback").textContent, /Type your answer/);
});

test("a step's suggested command can be typed into the terminal", () => {
  const view = quest(1);
  view.q(".step.is-current .type-command").click();
  assert.deepEqual(view.seen.typed, ["git status"]);
});

test("a read step continues on its button and a watch step waits for the repository", () => {
  const reading = quest(0);
  reading.q(".step.is-current .step-continue").click();
  assert.equal(reading.seen.continued, 1);
  const watching = quest(2);
  assert.equal(watching.q(".step.is-current form"), null);
  assert.match(watching.q(".step.is-current .step-watch").textContent, /Waiting/);
});

test("feedback shows the server's message, and a new step moves focus to it", () => {
  const view = quest(1);
  document.body.append(view.element);
  view.feedback([{ kind: "para", spans: [{ text: "Not quite.", code: false }] }], false);
  assert.match(view.q(".step-feedback").textContent, /Not quite\./);
  assert.ok(view.q(".step-feedback").classList.contains("is-wrong"));
  view.setStep(2);
  assert.match(view.q(".quest-count").textContent, /Step 3 of 3/);
  assert.equal(document.activeElement, view.q(".step.is-current h3"));
});

test("while busy the current step cannot be sent again", () => {
  const view = quest(1);
  view.busy(true);
  assert.equal(view.q(".step.is-current button[type=\"submit\"]").disabled, true);
  view.busy(false);
  assert.equal(view.q(".step.is-current button[type=\"submit\"]").disabled, false);
});
