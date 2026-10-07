"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { installBrowser, load, record } = require("./load");

const document = installBrowser();
const { Mission } = load(["dom.js", "markup.js", "art-pixels.js", "art-sprites.js", "mission.js"], ["Mission"]);

const para = (text) => [{ kind: "para", spans: [{ text, code: false }] }];

function mission({ level = record("level"), active = record("active") } = {}) {
  const seen = { answers: [], continued: 0, chosen: [], checks: [], hints: 0, typed: [] };
  const view = Mission.create({
    level,
    active,
    onAnswer: (text) => seen.answers.push(text),
    onContinue: () => (seen.continued += 1),
    onChoose: (value) => seen.chosen.push(value),
    onCheck: (answer) => seen.checks.push(answer),
    onHint: () => (seen.hints += 1),
    onType: (text) => seen.typed.push(text),
  });
  document.body.replaceChildren(view.element);
  const q = (selector) => view.element.querySelector(selector);
  const all = (selector) => [...view.element.querySelectorAll(selector)];
  return { view, seen, q, all };
}

test("the panel shows the brief, then the goals in order", () => {
  const run = mission();
  assert.match(run.q(".brief").textContent, /record the change to notes\.txt/);
  assert.equal(run.q("h3").textContent, "Goals");
  assert.equal(run.all(".goals .goal").length, 3);
});

test("goals before the current one are checked off, the current one is marked, and later ones wait", () => {
  const run = mission();
  const [first, second, third] = run.all(".goal");
  assert.ok(first.classList.contains("is-done"));
  assert.match(first.textContent, /\(done\)/);
  assert.ok(second.classList.contains("is-current"));
  assert.equal(third.className, "goal");
});

test("a goal that asks a question has its answer box while it is current, and sends the answer", () => {
  const run = mission();
  const form = run.q(".goal.is-current form");
  assert.match(form.textContent, /Which file has changes/);
  form.querySelector("input").value = "  notes.txt ";
  form.dispatchEvent(makeEvent("submit"));
  assert.deepEqual(run.seen.answers, ["notes.txt"]);
});

test("an empty answer is not sent", () => {
  const run = mission();
  run.q(".goal.is-current form").dispatchEvent(makeEvent("submit"));
  assert.deepEqual(run.seen.answers, []);
});

test("a goal to read has a Continue button while it is current", () => {
  const run = mission({ active: { ...record("active"), step: 0 } });
  run.q(".goal.is-current button.goal-continue").click();
  assert.equal(run.seen.continued, 1);
});

test("a goal the game watches for has no button: typing in the terminal passes it", () => {
  const run = mission({ active: { ...record("active"), step: 2 } });
  assert.equal(run.q(".goal.is-current button"), null);
  assert.equal(run.q(".goal.is-current input"), null);
});

test("moving to the next step redraws the goals", () => {
  const run = mission();
  run.view.setStep(2);
  assert.equal(run.all(".goal.is-done").length, 2);
  assert.ok(run.all(".goal")[2].classList.contains("is-current"));
});

test("after the steps, a level that asks a question adds it as the last goal, checked with the answer", () => {
  const level = { ...record("level"), question: para("Which commit added the file?"), placeholder: "a hash" };
  const run = mission({ level, active: { ...record("active"), step: 3 } });
  const last = run.all(".goal").at(-1);
  assert.ok(last.classList.contains("is-current"));
  assert.match(last.textContent, /Which commit added the file/);
  last.querySelector("input").value = "abc123";
  last.querySelector("form").dispatchEvent(makeEvent("submit"));
  assert.deepEqual(run.seen.checks, ["abc123"]);
});

test("a level without a question has no extra goal: the game checks the repository by itself", () => {
  const run = mission({ active: { ...record("active"), step: 3 } });
  assert.equal(run.all(".goal").length, 3);
  assert.equal(run.all(".goal.is-done").length, 3);
});

test("clicking a command in the panel types it in the terminal, without a prompt sign", () => {
  const run = mission();
  run.all(".goal")[1].querySelector("pre code").click();
  assert.deepEqual(run.seen.typed, ["git status"]);
});

test("a hint is asked for with a button, and revealed hints are listed", () => {
  const level = { ...record("level"), hints: [para("First hint.")] };
  const run = mission({ level, active: { ...record("active"), hints: 1 } });
  assert.deepEqual(run.all(".hint-list div").map((node) => node.textContent), ["First hint."]);
  assert.equal(run.q(".hint-row small").textContent, "A hint costs a star and this play's XP. 2 left.");
  run.q(".hint-row button").click();
  assert.equal(run.seen.hints, 1);
  run.view.addHint({ ...record("hint"), hint: para("Second hint."), used: 2 });
  assert.equal(run.all(".hint-list div").length, 2);
  assert.equal(run.q(".hint-row small").textContent, "That hint cost 10 XP. 1 left.");
});

test("once every hint is used the button is off", () => {
  const run = mission({ active: { ...record("active"), hints: 3 } });
  assert.equal(run.q(".hint-row button").disabled, true);
  assert.match(run.q(".hint-row small").textContent, /No hints left\.$/);
});

test("while a request runs the current goal's controls and the hint button are off", () => {
  const run = mission();
  run.view.busy(true);
  assert.equal(run.q(".goal.is-current button").disabled, true);
  assert.equal(run.q(".hint-row button").disabled, true);
  run.view.busy(false);
  assert.equal(run.q(".hint-row button").disabled, false);
});

test("a solved mission checks every goal", () => {
  const run = mission();
  run.view.solved();
  assert.equal(run.all(".goal.is-done").length, 3);
  assert.equal(run.q(".goal.is-current"), null);
});

test("a hint that cost nothing says so", () => {
  const run = mission();
  run.view.addHint({ ...record("hint"), cost: 0 });
  assert.equal(run.q(".hint-row small").textContent, "That hint cost no XP. 2 left.");
});

test("a note on the current goal shows under it, and the same note is not drawn twice", () => {
  const run = mission({ active: { ...record("active"), step: 2 } });
  run.view.note(para("No file is staged yet."));
  const note = run.q(".goal.is-current .goal-note");
  assert.equal(note.textContent, "No file is staged yet.");
  run.view.note(para("No file is staged yet."));
  assert.equal(run.q(".goal.is-current .goal-note"), note);
  run.view.setStep(3);
  assert.equal(run.q(".goal-note"), null);
});

const predict = () => {
  const level = record("level");
  level.steps[1] = { ...level.steps[1], kind: "choice", question: para("Where does the file go?"), choices: [{ value: "dock", text: para("To the dock") }, { value: "vault", text: para("Straight to the vault") }] };
  return level;
};

test("a prediction offers its choices as buttons under the goal, and sends the one clicked", () => {
  const run = mission({ level: predict() });
  const buttons = run.all(".goal.is-current .goal-choice");
  assert.deepEqual(buttons.map((button) => button.textContent), ["To the dock", "Straight to the vault"]);
  assert.match(run.q(".goal.is-current .goal-question").textContent, /Where does the file go/);
  buttons[1].click();
  assert.deepEqual(run.seen.chosen, ["vault"]);
});
