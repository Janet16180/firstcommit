"use strict";

/*
 * The live panel beside the terminal: the player's repository as a commit graph, the
 * stand-in GitHub when the level has one, the three areas strip, and "what just happened",
 * all from /api/observe (firstcommit/game.py's Observation). It redraws a part only when its
 * snapshot changed, and marks the commits that are new since the last drawing. Needs dom.js
 * and map.js. Defines one global, LivePanel.
 */

/* global Dom, RepoMap */
/* exported LivePanel */

const LivePanel = (function () {
  const { el } = Dom;
  const MAX_EVENTS = 40;
  const WORDS = {
    project: "Your repository",
    github: "GitHub (the practice copy)",
    areas: "The three areas",
    feed: "What just happened",
    quiet: "Nothing yet. Type a command in the terminal and watch this space.",
  };

  /* The feed after a new batch of events seen at `at`: the batch on top, in its own order. */
  const mergeEvents = (feed, events, at, max = MAX_EVENTS) => [...events.map((event) => ({ ...event, at })), ...feed].slice(0, max);

  const hashes = (snapshot) => new Set(snapshot.commits.map((commit) => commit.hash));

  /* options: theme (RepoMap's), words (this panel's titles), now (a clock), onChange({newCommits, events}). */
  function create({ theme = RepoMap.DEFAULT_THEME, words = {}, now = () => new Date(), onChange = () => {} } = {}) {
    const titles = { ...WORDS, ...words };
    const projectBox = el("div", { class: "live-map" });
    const githubBox = el("div", { class: "live-map" });
    const githubPart = el("section", { class: "live-part live-github", hidden: true, "aria-label": titles.github }, el("h3", {}, titles.github), githubBox);
    const areasBox = el("div", { class: "live-areas" });
    const feedList = el("ol", { class: "feed" });
    const quiet = el("p", { class: "feed-quiet" }, titles.quiet);
    const announce = el("p", { class: "sr-only", "aria-live": "polite" });
    const element = el("div", { class: "live" },
      el("div", { class: "live-maps" },
        el("section", { class: "live-part live-project", "aria-label": titles.project }, el("h3", {}, titles.project), projectBox),
        githubPart,
      ),
      el("div", { class: "live-lower" },
        el("section", { class: "live-part live-three", "aria-label": titles.areas }, el("h3", {}, titles.areas), areasBox),
        el("section", { class: "live-part live-feed", "aria-label": titles.feed }, el("h3", {}, titles.feed), quiet, feedList, announce),
      ),
    );
    const drawn = { project: null, github: null, files: null };
    let feed = [];

    function drawMap(box, key, snapshot, showHead) {
      const text = JSON.stringify(snapshot);
      if (drawn[key] === text) return 0;
      const previous = drawn[key] === null ? null : hashes(JSON.parse(drawn[key]));
      drawn[key] = text;
      box.replaceChildren(RepoMap.render(snapshot, { theme, previous, showHead }));
      return previous ? snapshot.commits.filter((commit) => !previous.has(commit.hash)).length : 0;
    }

    function drawAreas(files) {
      const text = JSON.stringify(files);
      if (drawn.files === text) return;
      drawn.files = text;
      areasBox.replaceChildren(RepoMap.renderAreas(files, { theme }));
    }

    function drawFeed(events) {
      if (!events.length) return;
      const at = now();
      feed = mergeEvents(feed, events, at);
      const time = (date) => date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      feedList.replaceChildren(...feed.map((event) => el("li", { "data-kind": event.kind, class: event.at === at ? "is-fresh" : null },
        el("time", {}, time(event.at)),
        el("span", {}, event.text),
      )));
      quiet.hidden = true;
      announce.textContent = events.map((event) => event.text).join(" ");
    }

    return {
      element,

      update(observation) {
        const newCommits = drawMap(projectBox, "project", observation.project, true);
        githubPart.hidden = observation.github === null;
        if (observation.github) drawMap(githubBox, "github", observation.github, false);
        drawAreas(observation.project.files);
        drawFeed(observation.events);
        onChange({ newCommits, events: observation.events });
      },
    };
  }

  return { create, mergeEvents };
})();
