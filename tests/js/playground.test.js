"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { installBrowser, load, record } = require("./load");

const document = installBrowser({ reducedMotion: true });
const { PlaygroundPanel, TimeShare } = load(
  ["dom.js", "markup.js", "map.js", "theme-time.js", "theme-time-motion.js", "theme-time-places.js", "theme-time-share.js", "playground.js"],
  ["PlaygroundPanel", "TimeShare"],
);

const button = (id, label, line, off = "") => ({ id, label, line, off });
const BUTTONS = {
  you: [button("edit:you.txt", "Edit you.txt", "echo 'A line from you' >> you.txt"), button("add:you.txt", "git add you.txt", "git add you.txt"), button("push", "git push", "git push")],
  alex: [button("edit:alex.txt", "Edit alex.txt", "echo 'A line from Alex' >> alex.txt"), button("pull", "git pull", "git pull"), button("push", "git push", "git push", "Alex has no commit GitHub lacks.")],
};
const observation = (buttons = BUTTONS) => ({ ...record("press").observation, buttons });
const para = (text) => [{ kind: "para", spans: [{ text, code: false }] }];

function pressView({ person = "alex", command = "git push", status = 0, output = "", explanation = null, fix = null, fixLine = "" } = {}) {
  const view = record("press");
  return { ...view, press: { ...view.press, person, command, status, output }, before: observation(), observation: observation(), explanation, fix, fix_line: fixLine };
}

/* A panel on the real share figure, its plays and the owner's callbacks recorded. */
function panel() {
  const seen = { presses: [], typed: [], plays: [], renders: [] };
  const share = {
    ...TimeShare,
    render: (state, options) => {
      seen.renders.push(options);
      return TimeShare.render(state, options);
    },
    play: (...args) => {
      const animation = { finished: 0, finish() { this.finished += 1; } };
      seen.plays.push({ args, animation });
      return [animation];
    },
  };
  const made = PlaygroundPanel.create({ share, onPress: (person, id) => seen.presses.push([person, id]), onType: (line) => seen.typed.push(line) });
  document.body.replaceChildren(made.element);
  const q = (selector) => made.element.querySelector(selector);
  const bar = (person) => made.element.querySelector(`[data-slot="${person}"] [role="toolbar"]`);
  const find = (person, label) => [...bar(person).querySelectorAll("button")].find((item) => item.textContent === label);
  const describedBy = (node) => document.getElementById(node.getAttribute("aria-describedby")).textContent;
  return { ...made, seen, q, bar, find, describedBy };
}

test("each person's buttons are a labelled toolbar in their own slot, each button described by its exact line", () => {
  const run = panel();
  run.draw(observation());
  assert.equal(run.bar("you").getAttribute("aria-label"), "Your buttons");
  assert.equal(run.bar("alex").getAttribute("aria-label"), "Alex's buttons");
  assert.deepEqual([...run.bar("you").querySelectorAll("button")].map((item) => item.textContent), ["Edit you.txt", "git add you.txt", "git push"]);
  assert.equal(run.describedBy(run.find("you", "Edit you.txt")), "echo 'A line from you' >> you.txt");
});

test("an off button stays focusable and says why; pressing it presses nothing", () => {
  const run = panel();
  run.draw(observation());
  const off = run.find("alex", "git push");
  assert.equal(off.getAttribute("aria-disabled"), "true");
  assert.equal(off.disabled, false);
  assert.equal(run.describedBy(off), "Alex has no commit GitHub lacks.");
  off.click();
  assert.deepEqual(run.seen.presses, []);
});

test("the line of the focused or hovered button, or why it is off, shows under its bar", () => {
  const run = panel();
  run.draw(observation());
  run.find("you", "git add you.txt").dispatchEvent(makeEvent("focus"));
  assert.equal(run.q('[data-slot="you"] .pg-line').textContent, "git add you.txt");
  run.find("alex", "git push").dispatchEvent(makeEvent("mouseenter"));
  assert.equal(run.q('[data-slot="alex"] .pg-line').textContent, "Alex has no commit GitHub lacks.");
});

test("a press goes to the owner, and nothing else is pressed until it is over", () => {
  const run = panel();
  run.draw(observation());
  run.find("you", "git add you.txt").click();
  assert.deepEqual(run.seen.presses, [["you", "add:you.txt"]]);
  run.busy(true);
  assert.ok([...run.element.querySelectorAll('[role="toolbar"] button')].every((item) => item.getAttribute("aria-disabled") === "true"));
  run.find("you", "git push").click();
  assert.deepEqual(run.seen.presses, [["you", "add:you.txt"]]);
  run.busy(false);
  assert.equal(run.find("you", "git push").getAttribute("aria-disabled"), null);
  assert.equal(run.find("alex", "git push").getAttribute("aria-disabled"), "true");
});

test("a press is played in the pressing person's computer, and focus stays on the pressed button", () => {
  const run = panel();
  const before = observation();
  run.draw(before);
  const pressed = run.find("alex", "Edit alex.txt");
  pressed.focus();
  pressed.click();
  const changed = (files) => files.map((entry, index) => (index === 0 ? { ...entry, folder: "f".repeat(40), folder_change: "modified" } : entry));
  const after = { ...observation(), teammate: { ...before.teammate, files: changed(before.teammate.files) }, teammate_events: [{ kind: "file-changed", text: para("alex.txt changed.") }] };
  run.draw(after, { person: "alex" });
  const [{ args }] = run.seen.plays;
  assert.deepEqual(args.slice(1, 4), [TimeShare.observed(before), TimeShare.observed(after), "alex"]);
  assert.deepEqual(args[4], TimeShare.pressed(before, after, "alex"));
  assert.equal(run.seen.renders.at(-1).person, "alex");
  assert.equal(document.activeElement, run.find("alex", "Edit alex.txt"));
});

test("a new press finishes the animations still running", () => {
  const run = panel();
  run.draw(observation());
  run.draw({ ...observation(), events: [{ kind: "file-changed", text: para("you.txt changed.") }], project: { ...observation().project, head: null } });
  const [{ animation }] = run.seen.plays;
  run.find("you", "git push").click();
  assert.equal(animation.finished, 1);
});

test("an observation that changed nothing is not drawn again", () => {
  const run = panel();
  run.draw(observation());
  const figure = run.q("figure");
  run.draw(observation());
  assert.equal(run.q("figure"), figure);
  assert.equal(run.seen.plays.length, 0);
});

test("whose buttons a narrow screen shows is kept when the figure is drawn again", () => {
  const run = panel();
  run.draw(observation());
  [...run.element.querySelectorAll(".ts-switch button")].find((item) => item.getAttribute("data-show") === "alex").click();
  run.draw(observation({ ...BUTTONS, you: BUTTONS.you.slice(0, 2) }));
  assert.equal(run.seen.renders.at(-1).shown, "alex");
  assert.equal(run.q("figure").getAttribute("data-shown"), "alex");
});

test("arrow keys move between the buttons of one bar, and only one of them is in the tab order", () => {
  const run = panel();
  run.draw(observation());
  const buttons = [...run.bar("you").querySelectorAll("button")];
  assert.deepEqual(buttons.map((item) => item.getAttribute("tabindex")), ["0", "-1", "-1"]);
  buttons[0].focus();
  buttons[0].dispatchEvent(makeEvent("keydown", { key: "ArrowRight" }));
  assert.equal(document.activeElement, buttons[1]);
  buttons[1].dispatchEvent(makeEvent("keydown", { key: "End" }));
  assert.equal(document.activeElement, buttons[2]);
  assert.deepEqual(buttons.map((item) => item.getAttribute("tabindex")), ["-1", "-1", "0"]);
});

test("the result says who ran what and the status in words, then git's output, the explanation and its fix button", () => {
  const run = panel();
  run.draw(observation());
  run.result(pressView({ status: 1, output: " ! [rejected]        main -> main (fetch first)\n", explanation: para("GitHub has a commit Alex does not."), fix: "pull" }));
  const result = run.q(".pg-result");
  assert.match(result.querySelector(".pg-ran").textContent, /Alex ran.*git push.*Git refused \(exit status 1\)/);
  assert.equal(result.querySelector("pre").textContent, " ! [rejected]        main -> main (fetch first)\n");
  assert.match(result.querySelector(".pg-explanation").textContent, /GitHub has a commit Alex does not\./);
  result.querySelector("button.pg-fix").click();
  assert.deepEqual(run.seen.presses, [["alex", "pull"]]);
});

test("a press that worked says done, with no output box when git printed nothing", () => {
  const run = panel();
  run.draw(observation());
  run.result(pressView());
  assert.match(run.q(".pg-ran").textContent, /Alex ran.*git push.*done/);
  assert.equal(run.q(".pg-result pre"), null);
});

test("the result is announced in one sentence in a polite live region", () => {
  const run = panel();
  run.draw(observation());
  run.result(pressView({ status: 1, explanation: para("GitHub has a commit Alex does not.") }));
  const region = run.q('[aria-live="polite"]');
  assert.equal(region.textContent, "Alex ran git push. Git refused, exit status 1. GitHub has a commit Alex does not.");
});

test("your presses offer their line and the fix's line to type in the terminal; Alex's do not", () => {
  const run = panel();
  run.draw(observation());
  run.result(pressView({ person: "you", command: "git push", status: 128, fixLine: "git push -u origin main" }));
  const typing = [...run.q(".pg-result").querySelectorAll("button.type-command")];
  typing.forEach((item) => item.click());
  assert.deepEqual(run.seen.typed, ["git push", "git push -u origin main"]);
  run.result(pressView({ person: "alex", fixLine: "git push -u origin main" }));
  assert.equal(run.q(".pg-result").querySelectorAll("button.type-command").length, 0);
});

test("a button the server found off says why in the result, and is announced", () => {
  const run = panel();
  run.draw(observation());
  run.refused("There is no notes.txt to delete.");
  assert.match(run.q(".pg-result").textContent, /There is no notes\.txt to delete\./);
  assert.equal(run.q('[aria-live="polite"]').textContent, "That button cannot be pressed now. There is no notes.txt to delete.");
});
