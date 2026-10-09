"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { createClock, installBrowser, load } = require("./load");

const document = installBrowser();
const { ViewBirth } = load(["dom.js", "strings.js", "births.js"], ["ViewBirth"]);

const reading = (vault) => ({ repository: vault !== null, workshop: [], dock: vault && [], vault, remote: null, crew: null });

/* A birth played on a bare sky, recording what was shown, what Rama said and the sky's classes at each step. */
function birth(view, { reducedMotion = false } = {}) {
  const clock = createClock();
  const sky = document.createElement("div");
  const seen = [];
  const finished = ViewBirth.play(view, {
    sky,
    reducedMotion,
    timers: clock,
    show: (shown) => seen.push(["show", shown]),
    say: (line) => seen.push(["say", line]),
  });
  return { clock, sky, seen, finished };
}

test("history is born as the chart alone, unrolling from your vault with Rama's line", async () => {
  const run = birth("history");
  assert.deepEqual(run.seen, [["show", "history"], ["say", "Here's the chart of every course."]]);
  assert.ok(run.sky.classList.contains("art-birth-unroll"));
  assert.equal(run.sky.style["--art-birth"], `${ViewBirth.BIRTH_MS}ms`);
  await run.clock.advance(ViewBirth.BIRTH_MS);
  await run.finished;
  assert.equal(run.seen.length, 2);
  assert.ok(!run.sky.classList.contains("art-birth-unroll"));
});

test("under reduced motion a birth is a still frame, held long enough to read its caption", async () => {
  const run = birth("history", { reducedMotion: true });
  assert.deepEqual(run.seen, [["show", "history"], ["say", "Here's the chart of every course."]]);
  assert.ok(!run.sky.classList.contains("art-birth-unroll"));
  await run.clock.advance(ViewBirth.STILL_MS);
  await run.finished;
  assert.equal(run.seen.length, 2);
});

test("only the views with a birth drawn have one", () => {
  assert.equal(ViewBirth.has("history"), true);
  for (const view of ["station", "crew", "board"]) assert.equal(ViewBirth.has(view), false, view);
});

test("history waits to be born until your vault holds commits, so the chart has something to unroll", () => {
  assert.equal(ViewBirth.ready("history", reading(null)), false);
  assert.equal(ViewBirth.ready("history", reading([])), false);
  assert.equal(ViewBirth.ready("history", reading([{ hash: "a" }])), true);
});

test("the crew band is born out of the crew view: Alex's station flattens into the band, with Rama's line", async () => {
  const run = birth("band");
  assert.deepEqual(run.seen, [["show", "flatten"], ["say", "Alex's station, flattened into a band: it still shows what reaches them."]]);
  assert.ok(run.sky.classList.contains("art-birth-flatten"));
  await run.clock.advance(ViewBirth.BIRTH_MS);
  await run.finished;
  assert.ok(!run.sky.classList.contains("art-birth-flatten"));
});

test("the band waits for a teammate on the stage", () => {
  assert.equal(ViewBirth.has("band"), true);
  assert.equal(ViewBirth.ready("band", reading([{ hash: "a" }])), false);
  assert.equal(ViewBirth.ready("band", { ...reading([]), crew: reading([]) }), true);
});

test("two sides are born when a conflict cracks open like a book, with Rama's line", async () => {
  const run = birth("sides");
  assert.deepEqual(run.seen, [["show", "sides"], ["say", "Your scanner has a docking mode: both sides, line by line."]]);
  assert.ok(run.sky.classList.contains("art-birth-book"));
  await run.clock.advance(ViewBirth.BIRTH_MS);
  await run.finished;
  assert.ok(!run.sky.classList.contains("art-birth-book"));
});

test("two sides wait for a file in conflict", () => {
  assert.equal(ViewBirth.has("sides"), true);
  assert.equal(ViewBirth.ready("sides", { ...reading([]), workshop: [{ path: "a.txt", state: "edited" }] }), false);
  assert.equal(ViewBirth.ready("sides", { ...reading([]), workshop: [{ path: "a.txt", state: "conflicted" }] }), true);
});

test("the black box is born as its level opens: a frame drawn round what Git keeps, with Rama's line", async () => {
  assert.equal(ViewBirth.has("blackbox"), true);
  assert.equal(ViewBirth.ready("blackbox", reading(null)), true);
  const run = birth("blackbox");
  assert.deepEqual(run.seen, [["show", "blackbox"], ["say", "Before anyone travels in time: a flight recorder."]]);
  assert.ok(run.sky.classList.contains("art-birth-boundary"));
  await run.clock.advance(ViewBirth.BIRTH_MS);
  await run.finished;
});

test("the tape is born in place on the level's first move of HEAD, with Rama's line", async () => {
  assert.equal(ViewBirth.has("tape"), true);
  assert.equal(ViewBirth.ready("tape", { ...reading([]), moved: false }), false);
  assert.equal(ViewBirth.ready("tape", { ...reading([]), moved: true }), true);
  const run = birth("tape");
  assert.deepEqual(run.seen, [["say", "The flight recorder keeps a tape: every move of HEAD, even to capsules no label holds."]]);
  assert.ok(run.sky.classList.contains("art-birth-tape"));
  await run.clock.advance(ViewBirth.BIRTH_MS);
  await run.finished;
});
