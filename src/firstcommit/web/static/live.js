"use strict";

/*
 * The live panel beside the terminal: the player's repository as a commit graph, the
 * stand-in GitHub when the level has one, the three areas strip, and "what just happened",
 * all from /api/observe (firstcommit/game.py's Observation). It redraws a part only when its
 * snapshot changed, and marks the commits that are new since the last drawing. On a playground
 * (an observation with the teammate's clone), the places part holds the playground panel
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
    places: "The four places",
    playground: "You, GitHub and Alex",
    feed: "What just happened",
    teammate: "On Alex's computer:",
    quiet: "Nothing yet. Type a command in the terminal and watch this space.",
  };

  /* The feed after a new batch of events seen at `at`: the batch on top, in its own order. */
  const mergeEvents = (feed, events, at, max = MAX_EVENTS) => [...events.map((event) => ({ ...event, at })), ...feed].slice(0, max);

  const hashes = (snapshot) => new Set(snapshot.commits.map((commit) => commit.hash));

  /* Names a part: its heading, and its section's label. */
  function retitle(heading, name) {
    heading.textContent = name;
    heading.parentNode.setAttribute("aria-label", name);
  }

  /* A feed event's words, after where it happened when that was the teammate's clone (`teammate`, the title saying so). */
  const where = (event, teammate) => (event.teammate ? `${teammate} ` : "");
  const time = (date) => date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

  /* The feed's items, those seen `at` marked fresh. */
  const feedItems = (feed, at, teammate) => feed.map((event) => el("li", { "data-kind": event.kind, class: event.at === at ? "is-fresh" : null },
    el("time", {}, time(event.at)),
    el("div", { class: "feed-text" }, event.teammate && el("span", { class: "feed-where" }, where(event, teammate)), Markup.render(event.text)),
  ));

  /* The panel's parts: the timelines cards, the feed and the three areas; with places, the places
     part first and the feed under it, and no cards. */
  function skeleton(titles, withPlaces) {
    const ui = {
      projectBox: el("div", { class: "live-map" }),
      githubBox: el("div", { class: "live-map" }),
      areasBox: el("div", { class: "live-areas" }),
      areasTitle: el("h3", {}, titles.areas),
      feedList: el("ol", { class: "feed" }),
      quiet: el("p", { class: "feed-quiet" }, titles.quiet),
      announce: el("p", { class: "sr-only", "aria-live": "polite" }),
    };
    ui.githubPart = el("section", { class: "live-part live-github", hidden: true, "aria-label": titles.github }, el("h3", {}, titles.github), ui.githubBox);
    const feedPart = el("section", { class: "live-part live-feed", "aria-label": titles.feed }, el("h3", {}, titles.feed), ui.quiet, ui.feedList, ui.announce);
    const areasPart = el("section", { class: "live-part live-three", "aria-label": titles.areas }, ui.areasTitle, ui.areasBox);
    const maps = el("div", { class: "live-maps" },
      el("section", { class: "live-part live-project", "aria-label": titles.project }, el("h3", {}, titles.project), ui.projectBox),
      ui.githubPart,
    );
    ui.element = withPlaces
      ? el("div", { class: "live has-places" }, areasPart, feedPart)
      : el("div", { class: "live" }, el("div", { class: "live-top" }, maps, feedPart), areasPart);
    return ui;
  }

  /* options: theme (RepoMap's), words (this panel's titles), now (a clock), onChange({newCommits, events}),
     play(figure, before, after, {theme, showHead}) to move a map redrawn after a change from its
     drawing before (the snapshots before and after), places ({commands, render, play}, as
     TimePlaces) to draw the player's places instead: they then hold the timelines too, so they
     take the maps' place at the top, with the feed under them, and the strip goes; and
     playground ({element, draw(observation, {person})}, as PlaygroundPanel), which takes the
     places' part for a lab with a teammate. */
  function create({ theme = RepoMap.DEFAULT_THEME, words = {}, now = () => new Date(), onChange = () => {}, play = () => {}, places = null, playground = null } = {}) {
    const titles = { ...WORDS, ...words };
    const { element, projectBox, githubBox, githubPart, areasBox, areasTitle, feedList, quiet, announce } = skeleton(titles, places !== null);
    const drawn = { project: null, github: null, files: null, places: null, playground: null };
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
       did light up, and the work moves from the drawing before. The part is the three areas until
       there is a GitHub, then the four places. */
    function drawPlaces({ project, github, events }) {
      const after = { project, github };
      const text = JSON.stringify(after);
      if (drawn.places === text) return 0;
      const before = drawn.places === null ? null : JSON.parse(drawn.places);
      drawn.places = text;
      const commands = before ? places.commands(events, before.project, project) : [];
      const figure = places.render(after, { commands });
      retitle(areasTitle, github ? titles.places : titles.areas);
      areasBox.replaceChildren(figure);
      if (!before) return 0;
      places.play(figure, { before, after, commands });
      const previous = hashes(before.project);
      return project.commits.filter((commit) => !previous.has(commit.hash)).length;
    }

    /* The playground in the places part, put there once; gives how many commits are new in your
       repository since the drawing before. */
    function drawPlayground(observation, person) {
      if (areasBox.firstChild !== playground.element) {
        areasBox.replaceChildren(playground.element);
        retitle(areasTitle, titles.playground);
      }
      const previous = drawn.playground && hashes(drawn.playground);
      drawn.playground = observation.project;
      playground.draw(observation, { person });
      return previous ? observation.project.commits.filter((commit) => !previous.has(commit.hash)).length : 0;
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
        let newCommits = 0;
        if (playground && observation.teammate) {
          newCommits = drawPlayground(observation, person);
        } else if (places) {
          newCommits = drawPlaces(observation);
        } else {
          newCommits = drawMap(projectBox, "project", observation.project, true);
          githubPart.hidden = observation.github === null;
          if (observation.github) drawMap(githubBox, "github", observation.github, false);
          drawAreas(observation.project.files);
        }
        drawFeed([...observation.events, ...observation.teammate_events.map((event) => ({ ...event, teammate: true }))]);
        onChange({ newCommits, events: observation.events });
      },
    };
  }

  return { create, mergeEvents };
})();
