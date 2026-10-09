"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

installBrowser();
const stored = new Map([["firstcommit.sound", "off"]]);
global.localStorage = { getItem: (key) => stored.get(key) ?? null, setItem: (key, value) => stored.set(key, value) };
const started = [];
class FakeParam {
  setValueAtTime() {}
  exponentialRampToValueAtTime() {}
  linearRampToValueAtTime() {}
}
class FakeNodeBase {
  constructor() {
    Object.assign(this, { gain: new FakeParam(), frequency: new FakeParam(), detune: new FakeParam(), Q: new FakeParam() });
  }

  connect(next) {
    return next;
  }

  start() {
    started.push(this.type || "node");
  }

  stop() {}
}
global.AudioContext = class {
  constructor() {
    Object.assign(this, { state: "running", currentTime: 0, sampleRate: 8000, destination: new FakeNodeBase() });
  }

  createOscillator() {
    return new FakeNodeBase();
  }

  createGain() {
    return new FakeNodeBase();
  }

  createBiquadFilter() {
    return new FakeNodeBase();
  }

  createDynamicsCompressor() {
    return Object.assign(new FakeNodeBase(), { threshold: new FakeParam(), knee: new FakeParam(), ratio: new FakeParam(), attack: new FakeParam(), release: new FakeParam() });
  }

  resume() {}
};
const fs = require("node:fs");
const path = require("node:path");
const { STATIC } = require("./load");
const { Sound } = load(["sound.js"], ["Sound"]);

test("the player's choice to mute is remembered", () => {
  assert.equal(Sound.isEnabled(), false);
  Sound.setEnabled(true);
  assert.equal(stored.get("firstcommit.sound"), "on");
});

test("nothing plays before the first click or key press, as browsers require", () => {
  Sound.setEnabled(true);
  Sound.play("correct");
  assert.equal(started.length, 0);
  Sound.unlock();
  Sound.play("correct");
  assert.ok(started.length > 0);
});

test("every sound the page uses exists, and muting silences them", () => {
  Sound.unlock();
  Sound.setEnabled(true);
  for (const name of Sound.NAMES) {
    const before = started.length;
    Sound.play(name);
    assert.ok(started.length > before, name);
  }
  Sound.setEnabled(false);
  const before = started.length;
  Sound.play("celebrate");
  assert.equal(started.length, before);
});

test("every sound a page script asks for exists", () => {
  const scripts = fs.readdirSync(STATIC).filter((name) => name.endsWith(".js"));
  const calls = scripts.flatMap((name) => [...fs.readFileSync(path.join(STATIC, name), "utf8").matchAll(/sound\.play\(([^)]*)\)/g)].map((match) => match[1]));
  const asked = calls.flatMap((call) => [...call.matchAll(/"(\w+)"/g)].map((match) => match[1]));
  assert.ok(asked.length > 5);
  for (const name of asked) assert.ok(Sound.NAMES.includes(name), name);
});

test("there is a sound for a typed command, a failed one, a goal, a lost star, a mission complete, the typewriter and a page turn", () => {
  for (const name of ["command", "failed", "goal", "starlost", "complete", "type", "page"]) assert.ok(Sound.NAMES.includes(name), name);
});
