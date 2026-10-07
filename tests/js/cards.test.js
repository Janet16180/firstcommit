"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { fakeServer, httpError, installBrowser, load, record, settle } = require("./load");

const document = installBrowser();
const { CardsView, createGameApi } = load(["dom.js", "strings.js", "markup.js", "api.js", "cards.js"], ["CardsView", "createGameApi"]);

const wrong = { ...record("card_result"), correct: false, xp: 0, streak: 0 };

function cards({ list = record("cards"), result = record("card_result"), chapter = "basics" } = {}) {
  const server = fakeServer({ "/api/cards": { cards: list }, "/api/card": result });
  const seen = { refreshed: 0 };
  const ctx = { game: createGameApi(server.api), status: () => record("status"), refresh: async () => (seen.refreshed += 1), sound: { play() {} } };
  const view = CardsView.create(ctx, chapter);
  document.body.replaceChildren(view.element);
  return { view, server, seen, q: (selector) => view.element.querySelector(selector), all: (selector) => [...view.element.querySelectorAll(selector)] };
}

const press = (run, key) => run.view.keydown(makeEvent("keydown", { key, target: document.body }));

test("the first card shows its prompt and numbered choices", async () => {
  const run = cards();
  await settle();
  assert.deepEqual(run.server.calls[0].path, "/api/cards?chapter=basics&limit=10");
  assert.match(run.q(".card-count").textContent, /Card 1 of 3 · The three areas/);
  assert.match(run.q(".card-prompt").textContent, /What does git add change\?/);
  assert.deepEqual(run.all("button.choice").map((button) => button.textContent), ["1The staging area", "2The last commit", "3The remote", "4Nothing until you push"]);
});

test("choosing sends the reply, then shows the explanation, the XP and the streak", async () => {
  const run = cards();
  await settle();
  run.all("button.choice")[0].click();
  await settle();
  assert.deepEqual(run.server.calls[1].body, { id: "sample-card-choice", reply: "The staging area" });
  assert.match(run.q(".card-result").textContent, /Right/);
  assert.match(run.q(".card-result").textContent, /copies the file into the staging area/);
  assert.match(run.q(".card-result").textContent, /\+5 XP/);
  assert.match(run.q(".card-result").textContent, /Streak: 3/);
  assert.ok(run.all("button.choice")[0].classList.contains("is-right"));
  assert.equal(run.seen.refreshed, 1);
});

test("a wrong reply shows the right answer as the server words it", async () => {
  const run = cards({ result: wrong });
  await settle();
  run.all("button.choice")[1].click();
  await settle();
  assert.match(run.q(".card-result").textContent, /Not this time.*The staging area/);
  assert.ok(run.all("button.choice")[1].classList.contains("is-wrong"));
  assert.ok(run.all("button.choice")[0].classList.contains("is-right"));
});

test("a card shows its level's name as the server words it", async () => {
  const run = cards({ list: [{ ...record("cards")[0], level: 2, level_name: "intermediate" }] });
  await settle();
  assert.equal(run.q(".card-level").textContent, "intermediate");
});

test("number keys pick a choice", async () => {
  const run = cards();
  await settle();
  press(run, "2");
  await settle();
  assert.deepEqual(run.server.calls[1].body, { id: "sample-card-choice", reply: "The last commit" });
});

test("a text card takes a typed reply, and a predict card shows its code", async () => {
  const [, typed, predict] = record("cards");
  const run = cards({ list: [typed, predict] });
  await settle();
  assert.equal(run.q("input").getAttribute("placeholder"), "a git command");
  run.q("input").value = " git status ";
  run.q("form").dispatchEvent(makeEvent("submit"));
  await settle();
  assert.deepEqual(run.server.calls[1].body, { id: "sample-card-text", reply: "git status" });
  run.q(".card-next").click();
  assert.match(run.q(".card-code").textContent, /git hash-object hello\.txt/);
  assert.equal(run.all("button.choice pre.code")[0].textContent, "ce013625030ba8dba906f756967f9e9ca394464a");
  assert.match(run.q(".card-pays").textContent, /no XP/);
});

test("after the last card a summary counts the right answers and the XP", async () => {
  const run = cards({ list: [record("cards")[0]] });
  await settle();
  run.all("button.choice")[0].click();
  await settle();
  run.q(".card-next").click();
  assert.match(run.q(".cards-summary").textContent, /1 of 1 right/);
  assert.match(run.q(".cards-summary").textContent, /\+5 XP/);
});

async function finishRound(run) {
  await settle();
  run.all("button.choice")[1].click();
  await settle();
  run.q(".card-next").click();
}

test("a round that paid nothing because no card was due says so", async () => {
  const notDue = { ...record("cards")[0], pays: false };
  const run = cards({ list: [notDue], result: { ...record("card_result"), xp: 0 } });
  await finishRound(run);
  assert.match(run.q(".cards-summary").textContent, /No XP this round: these cards were not due yet/);
});

test("a round of due cards that paid nothing does not blame the schedule", async () => {
  const run = cards({ list: [record("cards")[0]], result: wrong });
  await finishRound(run);
  assert.match(run.q(".cards-summary").textContent, /No XP this round\./);
  assert.doesNotMatch(run.q(".cards-summary").textContent, /not due/);
});

test("with no cards to review it says so", async () => {
  const run = cards({ list: [] });
  await settle();
  assert.match(run.view.element.textContent, /No cards to review/);
});

test("when the server does not answer, the card can be answered again", async () => {
  const run = cards({ result: httpError(0, "no answer") });
  await settle();
  run.all("button.choice")[0].click();
  await settle();
  assert.match(run.q(".card-result").textContent, /did not answer/);
  assert.equal(run.all("button.choice")[0].disabled, false);
});
