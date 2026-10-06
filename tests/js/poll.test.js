"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { createClock, installBrowser, load, record } = require("./load");

const page = installBrowser();
const { Polling } = load(["poll.js"], ["Polling"]);

const steps = record("level").steps;
const active = (step, count = steps.length) => ({ ...record("active"), step, steps: count });

test("while a watch step is current the page asks the server about that step", () => {
  assert.deepEqual(Polling.plan(steps, active(2)), { observe: true, watchStep: true, autoCheck: false });
});

test("answer and read steps wait for the player", () => {
  assert.deepEqual(Polling.plan(steps, active(0)), { observe: true, watchStep: false, autoCheck: false });
  assert.deepEqual(Polling.plan(steps, active(1)), { observe: true, watchStep: false, autoCheck: false });
});

test("once the quest is done, or when there is none, the level is checked automatically", () => {
  assert.deepEqual(Polling.plan(steps, active(3)), { observe: true, watchStep: false, autoCheck: true });
  assert.deepEqual(Polling.plan([], active(0, 0)), { observe: true, watchStep: false, autoCheck: true });
});

function counting(ms = 0, clock) {
  const ticks = [];
  const tick = () => {
    ticks.push(clock.now());
    return ms ? new Promise((resolve) => clock.setTimeout(resolve, ms)) : Promise.resolve();
  };
  return { tick, ticks };
}

test("it ticks at once, then again an interval after each tick has finished", async () => {
  const clock = createClock();
  const { tick, ticks } = counting(400, clock);
  const poller = Polling.start({ tick, intervalMs: 1500, timers: clock, page });
  await clock.advance(5000);
  poller.stop();
  assert.deepEqual(ticks, [0, 1900, 3800]);
});

test("stopping ends it, even in the middle of a tick", async () => {
  const clock = createClock();
  const { tick, ticks } = counting(400, clock);
  const poller = Polling.start({ tick, intervalMs: 1500, timers: clock, page });
  await clock.advance(100);
  poller.stop();
  await clock.advance(10000);
  assert.deepEqual(ticks, [0]);
  assert.equal(clock.pending(), 0);
});

test("it rests while the page is hidden and ticks again as soon as it is shown", async () => {
  const clock = createClock();
  const { tick, ticks } = counting(0, clock);
  const poller = Polling.start({ tick, intervalMs: 1500, timers: clock, page });
  await clock.advance(1000);
  page.hidden = true;
  await clock.advance(10000);
  assert.deepEqual(ticks, [0, 1500]);
  page.hidden = false;
  page.dispatchEvent(makeEvent("visibilitychange"));
  await clock.advance(0);
  assert.deepEqual(ticks, [0, 1500, 11000]);
  poller.stop();
  page.dispatchEvent(makeEvent("visibilitychange"));
  await clock.advance(5000);
  assert.equal(ticks.length, 3);
});

test("a page shown again in the middle of a tick starts no second tick", async () => {
  const clock = createClock();
  const { tick, ticks } = counting(400, clock);
  const poller = Polling.start({ tick, intervalMs: 1500, timers: clock, page });
  await clock.advance(50);
  page.hidden = true;
  page.dispatchEvent(makeEvent("visibilitychange"));
  page.hidden = false;
  page.dispatchEvent(makeEvent("visibilitychange"));
  await clock.advance(5000);
  poller.stop();
  assert.deepEqual(ticks, [0, 1900, 3800]);
});
