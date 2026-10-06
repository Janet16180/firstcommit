"use strict";

/*
 * Soft sound effects, synthesized with the Web Audio API (no audio files). Browsers allow
 * audio only after a user gesture, so nothing plays until `unlock()` runs on the first click
 * or key press; a sound asked for before that is skipped, not queued. The player's on/off
 * choice is a view preference kept in localStorage. Defines one global, Sound.
 */

/* exported Sound */

const Sound = (function () {
  const STORAGE_KEY = "firstcommit.sound";
  let context = null;
  let out = null;
  let unlocked = false;
  let enabled = readEnabled();

  function readEnabled() {
    try {
      return localStorage.getItem(STORAGE_KEY) !== "off";
    } catch (error) {
      return true; /* Storage is blocked: sound stays on for this visit. */
    }
  }

  function audio() {
    if (!context) {
      context = new window.AudioContext();
      out = context.createGain();
      out.gain.value = 0.5;
      const limiter = context.createDynamicsCompressor();
      limiter.threshold.value = -12;
      limiter.ratio.value = 12;
      out.connect(limiter).connect(context.destination);
    }
    if (context.state === "suspended") context.resume();
    return context;
  }

  /* One soft note: an oscillator with a quick attack and a long, gentle release. */
  function tone(at, { type = "sine", freq = 440, to = null, dur = 0.25, peak = 0.08, attack = 0.01 }) {
    const osc = context.createOscillator();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, at);
    if (to) osc.frequency.exponentialRampToValueAtTime(to, at + dur);
    const gain = context.createGain();
    gain.gain.setValueAtTime(0.0001, at);
    gain.gain.exponentialRampToValueAtTime(peak, at + attack);
    gain.gain.exponentialRampToValueAtTime(0.0001, at + dur);
    osc.connect(gain).connect(out);
    osc.start(at);
    osc.stop(at + dur + 0.05);
  }

  const note = (semitonesFromA4) => 440 * Math.pow(2, semitonesFromA4 / 12);
  const arpeggio = (at, steps, gap, options) => steps.forEach((step, index) => tone(at + index * gap, { ...options, freq: note(step) }));

  const PATCHES = {
    click: (at) => tone(at, { type: "triangle", freq: 1200, dur: 0.05, peak: 0.025 }),
    step: (at) => arpeggio(at, [3, 10], 0.09, { type: "triangle", dur: 0.3, peak: 0.06 }),
    correct: (at) => arpeggio(at, [3, 7, 10, 15], 0.08, { dur: 0.45, peak: 0.07 }),
    wrong: (at) => arpeggio(at, [-2, -6], 0.12, { type: "triangle", dur: 0.35, peak: 0.05 }),
    commit: (at) => {
      tone(at, { freq: note(15), dur: 0.5, peak: 0.05 });
      tone(at + 0.07, { freq: note(22), dur: 0.6, peak: 0.035 });
    },
    hint: (at) => arpeggio(at, [10, 15], 0.1, { dur: 0.6, peak: 0.04 }),
    card: (at) => tone(at, { type: "triangle", freq: 500, to: 900, dur: 0.12, peak: 0.03 }),
    celebrate: (at) => {
      arpeggio(at, [-9, -5, -2, 3, 7, 10, 15], 0.09, { type: "triangle", dur: 0.5, peak: 0.06 });
      [3, 7, 10, 15].forEach((step) => tone(at + 0.7, { freq: note(step), dur: 1.8, peak: 0.035, attack: 0.08 }));
    },
    rankup: (at) => arpeggio(at, [15, 19, 22, 27], 0.11, { type: "triangle", dur: 0.5, peak: 0.05 }),
  };

  function play(name) {
    if (!enabled || !unlocked || !window.AudioContext) return;
    if (audio().state === "running") PATCHES[name](context.currentTime + 0.01);
  }

  /* Runs on every pointer or key press; the first one allows audio for the rest of the visit. */
  function unlock() {
    unlocked = true;
  }

  function setEnabled(on) {
    enabled = on;
    try {
      localStorage.setItem(STORAGE_KEY, on ? "on" : "off");
    } catch (error) {
      /* Storage is blocked: the choice lasts for this visit. */
    }
  }

  return { NAMES: Object.keys(PATCHES), play, unlock, setEnabled, isEnabled: () => enabled };
})();
