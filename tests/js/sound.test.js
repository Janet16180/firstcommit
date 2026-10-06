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
