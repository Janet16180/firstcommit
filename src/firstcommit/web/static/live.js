"use strict";

/*
 * The live panel beside the terminal: the player's repository as a commit graph, the
 * stand-in GitHub when the level has one, the three areas strip, and "what just happened",
 * all from /api/observe (firstcommit/game.py's Observation). It redraws a part only when its
 * snapshot changed, and marks the commits that are new since the last drawing. On a playground
 * (an observation with the teammate's clone), the three areas part holds the playground panel
 * instead, and the teammate's events join the feed, each saying where it happened. Needs dom.js,
 * markup.js and map.js. Defines one global, LivePanel.
 */

/* global Dom, Markup, RepoMap */
/* exported LivePanel */

const LivePanel = (function () {
  const { el } = Dom;
  const MAX_EVENTS = 40;
  const WORDS = {
    project: "Your repository",
    github: "GitHub (the practice copy)",
    areas: "The three areas",
    playground: "You, GitHub and Alex",
    feed: "What just happened",
    teammate: "On Alex's computer:",
    quiet: "Nothing yet. Type a command in the terminal and watch this space.",
  };

  /* The feed after a new batch of events seen at `at`: the batch on top, in its own order. */
  const mergeEvents = (feed, events, at, max = MAX_EVENTS) => [...events.map((event) => ({ ...event, at })), ...feed].slice(0, max);

  const hashes = (snapshot) => new Set(snapshot.commits.map((commit) => commit.hash));

  /* A feed event's words, after where it happened when that was the teammate's clone (`teammate`, the title saying so). */
  const where = (event, teammate) => (event.teammate ? `${teammate} ` : "");
  const time = (date) => date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

  /* The feed's items, those seen `at` marked fresh. */
  const feedItems = (feed, at, teammate) => feed.map((event) => el("li", { "data-kind": event.kind, class: event.at === at ? "is-fresh" : null },
    el("time", {}, time(event.at)),
    el("div", { class: "feed-text" }, event.teammate && el("span", { class: "feed-where" }, where(event, teammate)), Markup.render(event.text)),
  ));

  /* options: theme (RepoMap's), words (this panel's titles), now (a clock), onChange({newCommits, events}),
     play(figure, before, after, {theme, showHead}) to move a map redrawn after a change from its
     drawing before (the snapshots before and after), places ({commands, render, play}, as
     TimePlaces) to draw the three areas as the player's places instead of the strip, and
     playground ({element, draw(observation, {person})}, as PlaygroundPanel) for a lab with a
     teammate. */
  function create({ theme = RepoMap.DEFAULT_THEME, words = {}, now = () => new Date(), onChange = () => {}, play = () => {}, places = null, playground = null } = {}) {
    const titles = { ...WORDS, ...words };
    const projectBox = el("div", { class: "live-map" });
    const githubBox = el("div", { class: "live-map" });
    const githubPart = el("section", { class: "live-part live-github", hidden: true, "aria-label": titles.github }, el("h3", {}, titles.github), githubBox);
    const areasBox = el("div", { class: "live-areas" });
    const areasTitle = el("h3", {}, titles.areas);
    const feedList = el("ol", { class: "feed" });
    const quiet = el("p", { class: "feed-quiet" }, titles.quiet);
    const announce = el("p", { class: "sr-only", "aria-live": "polite" });
    const element = el("div", { class: "live" },
      el("div", { class: "live-top" },
        el("div", { class: "live-maps" },
          el("section", { class: "live-part live-project", "aria-label": titles.project }, el("h3", {}, titles.project), projectBox),
          githubPart,
        ),
        el("section", { class: "live-part live-feed", "aria-label": titles.feed }, el("h3", {}, titles.feed), quiet, feedList, announce),
      ),
      el("section", { class: "live-part live-three", "aria-label": titles.areas }, areasTitle, areasBox),
    );
    const drawn = { project: null, github: null, files: null, places: null };
    let feed = [];

    function drawMap(box, key, snapshot, showHead) {
      const text = JSON.stringify(snapshot);
      if (drawn[key] === text) return 0;
      const before = drawn[key] === null ? null : JSON.parse(drawn[key]);
      const previous = before && hashes(before);
      drawn[key] = text;
      const figure = RepoMap.render(snapshot, { theme, previous, showHead });
      box.replaceChildren(figure);
      if (before) play(figure, before, snapshot, { theme, showHead });
      return previous ? snapshot.commits.filter((commit) => !previous.has(commit.hash)).length : 0;
    }

    function drawAreas(files) {
      const text = JSON.stringify(files);
      if (drawn.files === text) return;
      drawn.files = text;
      areasBox.replaceChildren(RepoMap.renderAreas(files, { theme }));
    }

    /* The places, redrawn when either repository changed: the arrows of what the batch's events
       did light up, and the work moves from the drawing before. */
    function drawPlaces({ project, github, events }) {
      const after = { project, github };
      const text = JSON.stringify(after);
      if (drawn.places === text) return;
      const before = drawn.places === null ? null : JSON.parse(drawn.places);
      drawn.places = text;
      const commands = before ? places.commands(events, before.project, project) : [];
      const figure = places.render(after, { commands });
      areasBox.replaceChildren(figure);
      if (before) places.play(figure, { before, after, commands });
    }

    /* The playground in the three areas part, put there once. */
    function drawPlayground(observation, person) {
      if (areasBox.firstChild !== playground.element) {
        areasBox.replaceChildren(playground.element);
        areasTitle.textContent = titles.playground;
      }
      playground.draw(observation, { person });
    }

    function drawFeed(events) {
      if (!events.length) return;
      const at = now();
      feed = mergeEvents(feed, events, at);
      feedList.replaceChildren(...feedItems(feed, at, titles.teammate));
      quiet.hidden = true;
      announce.textContent = events.map((event) => `${where(event, titles.teammate)}${Markup.plain(event.text)}`).join(" ");
    }

    return {
      element,

      /* Draws an observation; after a playground press, `person` is who pressed. */
      update(observation, { person = null } = {}) {
        const newCommits = drawMap(projectBox, "project", observation.project, true);
        githubPart.hidden = observation.github === null;
        if (observation.github) drawMap(githubBox, "github", observation.github, false);
        if (playground && observation.teammate) drawPlayground(observation, person);
        else if (places) drawPlaces(observation);
        else drawAreas(observation.project.files);
        drawFeed([...observation.events, ...observation.teammate_events.map((event) => ({ ...event, teammate: true }))]);
        onChange({ newCommits, events: observation.events });
      },
    };
  }

  return { create, mergeEvents };
})();
