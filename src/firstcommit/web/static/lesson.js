"use strict";

/*
 * The lesson player (firstcommit/game.py's LessonView). Each slide shows its text beside a
 * figure: the slide's commands with their real output, appearing one at a time at a pace the
 * player can read, and the repository they act on, shown as it was before them and then as
 * they left it, with what is new marked. Next first finishes a slide, then moves on; Space
 * pauses; under prefers-reduced-motion everything shows at once. A "places" slide draws your
 * computer's places (TimePlaces, handed in as `places`) and, once its commands have shown, lights
 * the arrows its change implies: the change the server tells for the slide (its `events`). Needs
 * dom.js, markup.js and map.js. Defines one global, LessonPlayer.
 */

/* global Dom, Markup, RepoMap */
/* exported LessonPlayer */

const LessonPlayer = (function () {
  const { el } = Dom;
  const FIRST_LINE_MS = 700;
  const NO_REPOSITORY = { exists: false, bare: false, head: null, branch: null, commits: [], refs: [], files: [], operation: null, stash: 0, truncated: false };

  /* How long a line stays the newest: long enough to read the command and its output. */
  const lineDelay = (line) => Math.min(5000, Math.max(1400, 800 + 25 * (line.command.length + line.output.length)));

  function transcript(lines, shown) {
    return el("ol", { class: "transcript", "aria-label": "Commands and their output" },
      lines.map((line, index) => el("li", { class: index < shown ? "transcript-line" : "transcript-line is-pending", "aria-hidden": index < shown ? null : "true" },
        el("code", { class: "transcript-command" }, el("span", { class: "prompt", "aria-hidden": "true" }, "$ "), line.command),
        line.output && el("pre", { class: "transcript-output" }, line.output.replace(/\n$/, "")),
      )),
    );
  }

  /* What a "places" slide shows: your repository before the slide's commands or after them (a
     lesson's frames hold no GitHub), and, after them, the commands its change lit. */
  function placesTransition(slide, before, places) {
    const [was, now] = [{ project: before.map, github: null }, { project: slide.map, github: null }];
    return { before: was, after: now, commands: places.commands(slide.events, before.map, slide.map) };
  }

  /* The repository part of the figure, before the slide's commands (`done` false) or after them. */
  function picture(slide, before, done, theme, places) {
    const map = done ? slide.map : before.map;
    const objects = done ? slide.objects : before.objects;
    const previousCommits = done ? new Set(before.map.commits.map((commit) => commit.hash)) : null;
    const previousObjects = done ? new Set(before.objects.map((object) => object.hash)) : null;
    const views = {
      map: () => RepoMap.render(map, { theme, previous: previousCommits }),
      areas: () => RepoMap.renderAreas(map.files, { theme }),
      objects: () => RepoMap.renderObjects(objects, { theme, previous: previousObjects }),
      places: () => {
        const { before: was, after: now, commands } = placesTransition(slide, before, places);
        return done ? places.render(now, { commands }) : places.render(was);
      },
    };
    return views[slide.view] ? views[slide.view]() : null;
  }

  /* Moves a slide's figure once its last command has shown: a map from the slide before's map,
     the places from the slide before's repository. */
  function move(figure, slide, before, { theme, play, places, reducedMotion }) {
    if (slide.view === "map") play(figure, before.map, slide.map, { theme, showHead: true });
    if (slide.view === "places") places.play(figure, placesTransition(slide, before, places), reducedMotion);
  }

  function skeleton(lesson, actions) {
    const ui = {
      count: el("p", { class: "kicker lesson-count", "aria-live": "polite" }),
      title: el("h2", { class: "lesson-title" }),
      text: el("div", { class: "lesson-text prose" }),
      figure: el("div", { class: "lesson-figure" }),
      backButton: el("button", { type: "button", class: "btn btn-ghost lesson-back", onclick: actions.back }, "Back"),
      pauseButton: el("button", { type: "button", class: "btn btn-quiet lesson-pause", onclick: actions.toggle }),
      nextButton: el("button", { type: "button", class: "btn btn-primary lesson-next", onclick: actions.next }),
      dots: el("ol", { class: "dots", "aria-hidden": "true" }),
    };
    ui.element = el("section", { class: "lesson panel", "aria-label": `Lesson: ${lesson.title}` },
      el("header", { class: "lesson-head" }, ui.count, ui.title, ui.dots),
      el("div", { class: "lesson-body" }, ui.text, ui.figure),
      el("footer", { class: "lesson-controls" }, ui.backButton, ui.pauseButton, ui.nextButton),
    );
    return ui;
  }

  /* options: lesson, theme, timers, reducedMotion, onFinish (after the last slide), onExit
     (Back on the first slide), play(figure, before, after, {theme, showHead}) to move a map
     slide's figure from the previous slide's map once its last command shows, and places
     ({commands, render, play}, as TimePlaces) to draw a "places" slide and play its change. */
  function create({ lesson, theme = RepoMap.DEFAULT_THEME, timers = window, reducedMotion = false, onFinish, onExit, play = () => {}, places = null }) {
    const { slides } = lesson;
    const { element, count, title, text, figure, pauseButton, nextButton, dots } = skeleton(lesson, { back: () => back(), toggle: () => toggle(), next: () => next() });
    let index = 0;
    let shown = 0;
    let playing = !reducedMotion;
    let timer = null;

    const slide = () => slides[index];
    const lines = () => (slide().view === "none" ? [] : slide().transcript);
    const done = () => shown >= lines().length;
    const before = () => (index > 0 ? slides[index - 1] : { map: NO_REPOSITORY, objects: [] });

    /* `finished`: the slide's last command has just shown, so a map or the places move from the
       slide before's. */
    function drawFigure(finished = false) {
      const visibleLines = lines();
      const repository = picture(slide(), before(), done(), theme, places);
      figure.replaceChildren(visibleLines.length ? transcript(visibleLines, shown) : "", repository || "");
      figure.hidden = !visibleLines.length && !repository;
      if (finished) move(repository, slide(), before(), { theme, play, places, reducedMotion });
    }

    function drawControls() {
      pauseButton.textContent = done() ? "Replay" : playing ? "Pause" : "Play";
      pauseButton.hidden = !lines().length;
      nextButton.textContent = index === slides.length - 1 ? "Start the practice" : "Next";
    }

    function schedule() {
      timers.clearTimeout(timer);
      timer = null;
      if (!playing || done()) return;
      const wait = shown === 0 ? FIRST_LINE_MS : lineDelay(lines()[shown - 1]);
      timer = timers.setTimeout(() => {
        shown += 1;
        drawFigure(done());
        drawControls();
        schedule();
      }, wait);
    }

    function show(target, complete) {
      index = target;
      shown = complete ? lines().length : 0;
      count.textContent = `Lesson · ${index + 1} of ${slides.length}`;
      title.textContent = slide().title;
      text.replaceChildren(...Markup.render(slide().text), Markup.more(slide().more) || "");
      dots.replaceChildren(...slides.map((_, dot) => el("li", { class: dot === index ? "is-on" : dot < index ? "is-done" : null })));
      drawFigure();
      drawControls();
      schedule();
    }

    function next() {
      if (!done()) return show(index, true);
      if (index === slides.length - 1) return onFinish();
      return show(index + 1, reducedMotion);
    }

    function back() {
      if (index === 0) return onExit();
      return show(index - 1, true);
    }

    function toggle() {
      if (done()) {
        playing = !reducedMotion;
        return show(index, reducedMotion);
      }
      playing = !playing;
      drawControls();
      return schedule();
    }

    show(0, reducedMotion);

    return {
      element,

      /* Arrows move between slides and Space pauses, except in a text field, and Space on a
         button or link presses it as usual. */
      keydown(event) {
        const actions = { ArrowRight: next, ArrowLeft: back, " ": toggle };
        const typing = event.target.closest("input, textarea");
        const pressing = event.key === " " && event.target.closest("button, a, summary");
        if (!actions[event.key] || event.altKey || event.ctrlKey || event.metaKey || typing || pressing) return;
        event.preventDefault();
        actions[event.key]();
      },

      dispose() {
        timers.clearTimeout(timer);
      },
    };
  }

  return { create, lineDelay, FIRST_LINE_MS };
})();
