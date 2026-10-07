"use strict";

/*
 * Loads page scripts into the test file's own realm, in order, as script tags would: the names a
 * script declares at its top level become globals the next script sees. node --test runs each
 * test file in its own process, so every file starts from a clean page.
 */

const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { createDocument } = require("./fakedom");

const STATIC = path.join(__dirname, "..", "..", "src", "firstcommit", "web", "static");
const RECORDS = JSON.parse(fs.readFileSync(path.join(__dirname, "records.json"), "utf8"));

/* A fresh deep copy of one sample record (tests may change what they get). */
const record = (name) => structuredClone(RECORDS[name]);

/* Installs a fake document and the few window functions the scripts use; reduced motion is on by default. */
function installBrowser({ reducedMotion = true } = {}) {
  global.document = createDocument();
  global.window = global;
  global.matchMedia = (query) => ({
    matches: query.includes("reduce") ? reducedMotion : false,
    addEventListener() {},
  });
  global.requestAnimationFrame = (callback) => setTimeout(() => callback(0), 0);
  return global.document;
}

/* Runs the scripts in order and returns the globals named in `take`. */
function load(scripts, take) {
  for (const name of scripts) vm.runInThisContext(fs.readFileSync(path.join(STATIC, name), "utf8"), { filename: name });
  return Object.fromEntries(take.map((name) => [name, vm.runInThisContext(name)]));
}

/* Lets pending promise callbacks run. */
const settle = () => new Promise((resolve) => setImmediate(resolve));

/* Timers a test moves by hand: `advance(ms)` runs every timer that falls due, in order, settling
   promises after each one. */
function createClock() {
  let now = 0;
  let nextId = 1;
  const timers = new Map();
  return {
    setTimeout(callback, ms = 0) {
      timers.set(nextId, { at: now + ms, callback });
      nextId += 1;
      return nextId - 1;
    },
    clearTimeout(id) {
      timers.delete(id);
    },
    now: () => now,
    pending: () => timers.size,
    async advance(ms) {
      const end = now + ms;
      await settle();
      for (;;) {
        const due = [...timers].filter(([, timer]) => timer.at <= end).sort((a, b) => a[1].at - b[1].at || a[0] - b[0])[0];
        if (!due) break;
        timers.delete(due[0]);
        now = due[1].at;
        due[1].callback();
        await settle();
      }
      now = end;
    },
  };
}

/* A stand-in for client.js's `api`: answers from `replies` (path -> value or function of the body),
   and records every call. A reply that is an Error is thrown. */
function fakeServer(replies) {
  const calls = [];
  async function api(target, body) {
    calls.push({ path: target, body });
    const route = target.split("?")[0];
    if (!(route in replies)) throw Object.assign(new Error(`no reply for ${route}`), { status: 404 });
    const reply = typeof replies[route] === "function" ? replies[route](body, target) : replies[route];
    if (reply instanceof Error) throw reply;
    return structuredClone(reply);
  }
  return { api, calls };
}

/* An error as client.js throws it for an HTTP status, with the server's reply as `data`. */
const httpError = (status, message = `status ${status}`, data = {}) => Object.assign(new Error(message), { status, data });

/* The two-person playground's real buttons (records.json's press), some made off: {person: {id: reason}}. */
function playgroundButtons(off = {}) {
  const buttons = record("press").observation.buttons;
  for (const [person, reasons] of Object.entries(off)) buttons[person] = buttons[person].map((view) => (view.id in reasons ? { ...view, off: reasons[view.id] } : view));
  return buttons;
}

/* An observation of the two-person playground, with each person's buttons. */
const playgroundObservation = (buttons = playgroundButtons()) => ({ ...record("press").observation, buttons });

/* A press's reply (PressView), as the server sends it once the playground explains presses. */
function pressView({ person = "alex", command = "git push", status = 0, output = "", explanation = null, fix = null, fixLine = "", before = playgroundObservation(), after = playgroundObservation() } = {}) {
  const view = record("press");
  return { ...view, press: { ...view.press, person, command, status, output }, before, observation: after, explanation, fix, fix_line: fixLine };
}

module.exports = { STATIC, RECORDS, record, installBrowser, load, settle, createClock, fakeServer, httpError, playgroundButtons, playgroundObservation, pressView };
