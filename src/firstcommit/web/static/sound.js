"use strict";

/*
 * Soft 8-bit sound effects, synthesized with the Web Audio API (no audio files). Browsers allow
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

  /* 8-bit voices: square and triangle waves, short and quiet. Every sound only echoes something
     the screen also shows, so a player who hears nothing misses nothing. */
  const blip = (at, freq, dur, peak = 0.025, type = "square") => tone(at, { type, freq, dur, peak, attack: 0.005 });
  const PATCHES = {
    /* A line typed in the terminal ran (the terminal shows it). */
    command: (at) => blip(at, note(15), 0.05, 0.018),
    /* A line typed in the terminal failed (the terminal shows the error). */
    failed: (at) => arpeggio(at, [-14, -17], 0.07, { type: "square", dur: 0.09, peak: 0.022, attack: 0.005 }),
    /* A goal ticked (its box fills). */
    goal: (at) => arpeggio(at, [7, 12, 19], 0.06, { type: "square", dur: 0.08, peak: 0.025, attack: 0.005 }),
    /* A star lost (the head's stars shake). */
    starlost: (at) => arpeggio(at, [12, 7, 0], 0.08, { type: "triangle", dur: 0.12, peak: 0.04, attack: 0.005 }),
    /* A mission complete (the band and the dock). */
    complete: (at) => {
      arpeggio(at, [0, 4, 7, 12, 16, 19], 0.07, { type: "square", dur: 0.1, peak: 0.025, attack: 0.005 });
      blip(at + 0.45, note(24), 0.4, 0.025, "triangle");
    },
    /* Rama's typewriter in a scene (the letters appear). */
    type: (at) => blip(at, note(27), 0.02, 0.01),
    /* A scene's next page (the picture and line change). */
    page: (at) => tone(at, { type: "triangle", freq: note(10), to: note(17), dur: 0.08, peak: 0.025, attack: 0.005 }),
    /* An answer right or wrong (the feedback line says so). */
    correct: (at) => arpeggio(at, [12, 19], 0.07, { type: "square", dur: 0.09, peak: 0.025, attack: 0.005 }),
    wrong: (at) => arpeggio(at, [-2, -6], 0.1, { type: "triangle", dur: 0.14, peak: 0.04, attack: 0.005 }),
    /* A hint shown, a card turned (both on screen). */
    hint: (at) => arpeggio(at, [10, 15], 0.08, { type: "triangle", dur: 0.14, peak: 0.035, attack: 0.005 }),
    card: (at) => blip(at, note(5), 0.05, 0.02, "triangle"),
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
