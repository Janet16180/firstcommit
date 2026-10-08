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

test("history is born out of your station: the fold, then the unroll, each with Rama's line", async () => {
  const run = birth("history");
  assert.deepEqual(run.seen, [["show", "fold"], ["say", "You know every room now."]]);
  assert.ok(run.sky.classList.contains("art-birth-fold"));
  assert.equal(run.sky.style["--art-birth"], `${ViewBirth.BIRTH_MS}ms`);
  await run.clock.advance(ViewBirth.BIRTH_MS);
  assert.deepEqual(run.seen.slice(2), [["show", "history"], ["say", "Here's the chart of every course."]]);
  assert.ok(!run.sky.classList.contains("art-birth-fold"));
  assert.ok(run.sky.classList.contains("art-birth-unroll"));
  await run.clock.advance(ViewBirth.BIRTH_MS);
  await run.finished;
  assert.ok(!run.sky.classList.contains("art-birth-unroll"));
});

test("under reduced motion a birth is two still frames, each held long enough to read its caption", async () => {
  const run = birth("history", { reducedMotion: true });
  assert.deepEqual(run.seen, [["show", "fold"], ["say", "You know every room now."]]);
  assert.ok(!run.sky.classList.contains("art-birth-fold"));
  await run.clock.advance(ViewBirth.BIRTH_MS);
  assert.equal(run.seen.length, 2);
  await run.clock.advance(ViewBirth.STILL_MS - ViewBirth.BIRTH_MS);
  assert.deepEqual(run.seen.slice(2), [["show", "history"], ["say", "Here's the chart of every course."]]);
  assert.ok(!run.sky.classList.contains("art-birth-unroll"));
  await run.clock.advance(ViewBirth.STILL_MS);
  await run.finished;
});

test("only the views with a birth drawn have one", () => {
  assert.equal(ViewBirth.has("history"), true);
  for (const view of ["station", "crew", "blackbox"]) assert.equal(ViewBirth.has(view), false, view);
});

test("history waits to be born until your vault holds commits, so the fold has something to fold", () => {
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
