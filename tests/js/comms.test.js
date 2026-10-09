"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const { Comms } = load(["dom.js", "strings.js", "markup.js", "art-pixels.js", "art-sprites.js", "comms.js"], ["Comms"]);

const para = (text) => [{ kind: "para", spans: [{ text, code: false, em: false }] }];

test("Rama's line shows Rama, who is speaking, and is announced politely", () => {
  const comms = Comms.create();
  assert.ok(comms.element.querySelector("svg.art-rama"));
  assert.equal(comms.element.querySelector(".comms-who").textContent, "Rama, ship's computer");
  assert.equal(comms.element.getAttribute("aria-live"), "polite");
});

test("Rama says plain text or the game's text blocks, with a mood", () => {
  const comms = Comms.create();
  comms.say("Hello.");
  assert.equal(comms.element.querySelector(".comms-text").textContent, "Hello.");
  assert.equal(comms.element.dataset.mood, "info");
  comms.say(para("Not quite."), "err");
  assert.equal(comms.element.querySelector(".comms-text").textContent, "Not quite.");
  assert.equal(comms.element.dataset.mood, "err");
});

test("saying the same thing again leaves the line alone, so it is not announced twice", () => {
  const comms = Comms.create();
  comms.say(para("Waiting."), "info");
  const shown = comms.element.querySelector(".comms-text p");
  comms.say(para("Waiting."), "info");
  assert.equal(comms.element.querySelector(".comms-text p"), shown);
});

test("an unknown mood is refused", () => {
  assert.throws(() => Comms.create().say("Hi.", "happy"), /mood/);
});
