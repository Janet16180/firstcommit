"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { createClock, installBrowser, load, record } = require("./load");

installBrowser();
const { LessonPlayer, TimePlaces } = load(["dom.js", "markup.js", "map.js", "theme-time.js", "theme-time-motion.js", "theme-time-places.js", "lesson.js"], ["LessonPlayer", "TimePlaces"]);

/* A lesson player, moved on with Next to the slide numbered `slide` (from 1). */
function player({ reducedMotion = false, onFinish = () => {}, onExit = () => {}, slide = 1, play, lesson = record("lesson"), places } = {}) {
  const clock = createClock();
  const made = LessonPlayer.create({ lesson, timers: clock, reducedMotion, onFinish, onExit, play, places });
  const view = { ...made, clock, lesson, q: (selector) => made.element.querySelector(selector), all: (selector) => [...made.element.querySelectorAll(selector)] };
  while (!view.q(".lesson-count").textContent.includes(`${slide} of`)) view.q(".lesson-next").click();
  return view;
}

const shownLines = (view) => view.all(".transcript-line").filter((line) => !line.classList.contains("is-pending")).length;
const press = (view, key) => view.keydown(makeEvent("keydown", { key, target: view.element }));

test("a slide shows its title, its text and where it is in the lesson", () => {
  const view = player();
  assert.match(view.q(".lesson-count").textContent, /1 of 5/);
  assert.equal(view.q(".lesson-title").textContent, view.lesson.slides[0].title);
  assert.match(view.q(".lesson-text").textContent, /adds a hidden/);
});

test("the slide's commands appear one at a time, at a pace the player can read", async () => {
  const view = player();
  assert.equal(shownLines(view), 0);
  assert.equal(view.all(".transcript-line").length, 3);
  await view.clock.advance(LessonPlayer.FIRST_LINE_MS);
  assert.equal(shownLines(view), 1);
  await view.clock.advance(LessonPlayer.lineDelay(view.lesson.slides[0].transcript[0]));
  assert.equal(shownLines(view), 2);
  assert.match(view.q(".transcript").textContent, /git init -q/);
});

test("the figure shows the repository before the commands, then after them with what is new", async () => {
  const view = player({ slide: 3 });
  assert.equal(view.all(".map-commit").length, 0);
  assert.match(view.q(".lesson-figure").textContent, /no commits yet/);
  await view.clock.advance(60000);
  assert.equal(view.all(".map-commit").length, 1);
  assert.equal(view.all(".map-commit.is-new").length, 1);
});

test("Next first finishes the slide, then moves on", () => {
  const view = player();
  view.q(".lesson-next").click();
  assert.equal(shownLines(view), 3);
  assert.match(view.q(".lesson-count").textContent, /1 of 5/);
  view.q(".lesson-next").click();
  assert.match(view.q(".lesson-count").textContent, /2 of 5/);
  assert.equal(shownLines(view), 0);
});

test("Back shows the previous slide finished, and the first slide's Back leaves the lesson", () => {
  let left = 0;
  const view = player({ onExit: () => (left += 1), slide: 2 });
  view.q(".lesson-back").click();
  assert.match(view.q(".lesson-count").textContent, /1 of 5/);
  assert.equal(view.all(".transcript-line.is-pending").length, 0);
  view.q(".lesson-back").click();
  assert.equal(left, 1);
});

test("with reduced motion every line and the final figure show at once", () => {
  const view = player({ reducedMotion: true, slide: 3 });
  assert.equal(shownLines(view), 2);
  assert.equal(view.all(".map-commit").length, 1);
});

test("pausing stops the lines, and playing goes on", async () => {
  const view = player();
  press(view, " ");
  await view.clock.advance(20000);
  assert.equal(shownLines(view), 0);
  assert.match(view.q(".lesson-pause").textContent, /Play/);
  view.q(".lesson-pause").click();
  await view.clock.advance(LessonPlayer.FIRST_LINE_MS);
  assert.equal(shownLines(view), 1);
});

test("the arrow keys move between slides", () => {
  const view = player();
  press(view, "ArrowRight");
  press(view, "ArrowRight");
  assert.match(view.q(".lesson-count").textContent, /2 of 5/);
  press(view, "ArrowLeft");
  assert.match(view.q(".lesson-count").textContent, /1 of 5/);
});

test("each kind of figure shows what it should", () => {
  const kinds = [1, 2, 3, 4, 5].map((slide) => {
    const view = player({ reducedMotion: true, slide });
    return [
      Boolean(view.q(".transcript")),
      Boolean(view.q("svg.map-graph") || view.q(".map-empty")),
      Boolean(view.q(".areas")),
      Boolean(view.q("table.objects")),
    ];
  });
  assert.deepEqual(kinds, [
    [true, false, false, false],
    [true, false, true, false],
    [true, true, false, false],
    [false, false, false, true],
    [false, false, false, false],
  ]);
});

test("the last slide's Next finishes the lesson", () => {
  let finished = 0;
  const view = player({ reducedMotion: true, slide: 5, onFinish: () => (finished += 1) });
  assert.match(view.q(".lesson-next").textContent, /practice/i);
  view.q(".lesson-next").click();
  assert.equal(finished, 1);
});

test("objects new since the previous slide are marked", () => {
  const view = player({ reducedMotion: true, slide: 4 });
  assert.equal(view.all("table.objects tr.is-new").length, 0);
  const commitSlide = player({ reducedMotion: true, slide: 3 });
  assert.equal(commitSlide.all(".map-commit.is-new").length, 1);
});

test("a map slide moves from the previous slide's map when its last command shows, and again on Replay", async () => {
  const plays = [];
  const view = player({ slide: 3, play: (figure, before, after, options) => plays.push({ figure, before, after, options }) });
  const finish = async () => {
    await view.clock.advance(LessonPlayer.FIRST_LINE_MS);
    await view.clock.advance(LessonPlayer.lineDelay(view.lesson.slides[2].transcript[0]));
  };
  await finish();
  assert.equal(plays.length, 1);
  assert.equal(plays[0].figure, view.q(".lesson-figure .repo-map"));
  assert.deepEqual([plays[0].before, plays[0].after, plays[0].options.showHead], [view.lesson.slides[1].map, view.lesson.slides[2].map, true]);
  view.q(".lesson-pause").click();
  await finish();
  assert.equal(plays.length, 2, "Replay plays it again");
});

test("a slide shown finished at once does not move: Next pressed early, Back, or reduced motion", async () => {
  const plays = [];
  const play = () => plays.push(1);
  const early = player({ slide: 3, play });
  early.q(".lesson-next").click();
  const back = player({ slide: 4, play });
  back.q(".lesson-back").click();
  player({ slide: 3, play, reducedMotion: true });
  await early.clock.advance(10000);
  assert.deepEqual(plays, []);
});

/* The sample lesson with its commit slide (the third) drawn as the places, and the change the
   server tells for it: the commit of the file the slide before staged. */
function placesLesson() {
  const lesson = record("lesson");
  lesson.slides[2] = { ...lesson.slides[2], view: "places", events: [{ kind: "commit-created", text: [] }] };
  return lesson;
}

/* TimePlaces, with every play() recorded instead of run. */
function recordingPlaces(plays) {
  return { ...TimePlaces, play: (figure, transition, reduced) => plays.push({ figure, transition, reduced }) };
}

const finishCommitSlide = async (view) => {
  await view.clock.advance(LessonPlayer.FIRST_LINE_MS);
  for (const line of view.lesson.slides[2].transcript) await view.clock.advance(LessonPlayer.lineDelay(line));
};

test("a places slide draws your computer's places from the slide's repository: before its commands, then as they left it, with no GitHub", async () => {
  const view = player({ slide: 3, lesson: placesLesson(), places: TimePlaces });
  assert.ok(view.q(".lesson-figure .tt-places.is-local"));
  assert.equal(view.q(".tt-frame.is-github"), null);
  assert.equal(view.all(".tt-places .map-commit").length, 0, "before the commit");
  await finishCommitSlide(view);
  assert.equal(view.all(".tt-places .map-commit").length, 1, "after it");
  const graphs = view.all(".lesson-figure .map-graph");
  assert.ok(graphs.length > 0 && graphs.every((graph) => graph.closest(".tt-places")), "no map besides the places' own");
});

test("once its commands have shown, a places slide lights the arrows its change implies and says what they do", async () => {
  const view = player({ slide: 3, lesson: placesLesson(), places: TimePlaces });
  assert.equal(view.q(".tt-arrow.is-active"), null);
  await finishCommitSlide(view);
  assert.deepEqual(view.all(".tt-arrow.is-active").map((node) => node.getAttribute("data-command")), ["commit"]);
  assert.match(view.q(".tt-places-caption").textContent, /saves the staging area as a new commit/);
});

test("a places slide plays its change from the previous slide's repository when its last command shows, and again on Replay", async () => {
  const plays = [];
  const view = player({ slide: 3, lesson: placesLesson(), places: recordingPlaces(plays) });
  await finishCommitSlide(view);
  assert.equal(plays.length, 1);
  const [{ figure, transition, reduced }] = plays;
  assert.equal(figure, view.q(".lesson-figure .tt-places"));
  assert.deepEqual(transition, { before: { project: view.lesson.slides[1].map, github: null }, after: { project: view.lesson.slides[2].map, github: null }, commands: ["commit"] });
  assert.equal(reduced, false);
  view.q(".lesson-pause").click();
  await finishCommitSlide(view);
  assert.equal(plays.length, 2, "Replay plays it again");
});

test("a places slide shown finished at once does not move, but still lights its arrows: Next pressed early, Back, or reduced motion", async () => {
  const plays = [];
  const places = recordingPlaces(plays);
  const early = player({ slide: 3, lesson: placesLesson(), places });
  early.q(".lesson-next").click();
  const back = player({ slide: 4, lesson: placesLesson(), places });
  back.q(".lesson-back").click();
  const still = player({ slide: 3, lesson: placesLesson(), places, reducedMotion: true });
  await early.clock.advance(10000);
  assert.deepEqual(plays, []);
  for (const view of [early, back, still]) assert.ok(view.q(".tt-arrow.is-commit.is-active"));
});
