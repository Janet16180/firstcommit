"use strict";

/*
 * The four places: your computer (working folder, staging area, your repository) next to
 * GitHub (the remote repository), with an arrow for each command that moves work between them:
 * add, commit, push, fetch, pull and clone. Everything drawn is the player's own: the files of
 * the three areas (RepoMap.areaRows, the rule the three areas strip uses) and the two commit
 * graphs, drawn by the map renderer at a small size, origin/main included.
 *
 * commands(events, before, after) says which arrows match what just happened, from the feed's
 * own event kinds and your repository's two snapshots; flights(before, after, commands) says
 * what travels along them: the files and commits that really changed place between the two
 * observations. Both are pure. render(...) draws the figure, lights those arrows and shows their
 * sentences; play(...) runs the flights and the commit graphs' own motions
 * (theme-time-motion.js). Every sentence is checked against git 2.43
 * (docs-draft/four-places.md). Needs dom.js, map.js, theme-time.js and theme-time-motion.js.
 * Defines one global, TimePlaces.
 */

/* global Dom, RepoMap, TimeTheme, TimeMotion */
/* exported TimePlaces */

const TimePlaces = (function () {
  const { el } = Dom;

  /* The places in the order work travels towards GitHub. */
  const PLACES = {
    folder: "Working folder",
    index: "Staging area",
    repository: "Your repository",
    remote: "Remote repository",
  };
  const COMPUTER = "Your computer";
  const GITHUB = "GitHub (the practice copy)";
  const NO_REMOTE = "No remote yet.";

  /* Each command's arrow: the places its work passes, first to last, and the checked sentence
     shown when it lights (A1 to A6). The pull arrow is pull's merge half: its fetch half is the
     fetch arrow, which lights with it. */
  const ARROWS = {
    add: { path: ["folder", "index"], text: "`add` copies a file's current content from the working folder into the staging area; the working folder keeps it." },
    commit: { path: ["index", "repository"], text: "`commit` saves the staging area as a new commit in your repository; the staging area keeps its files. Your branch moves onto the new commit, and `origin/main` does not move." },
    push: { path: ["repository", "remote"], text: "`push` sends the commits GitHub is missing and moves GitHub's branch to your commit; your `origin/main` moves to match. Git refuses a push that is not a fast-forward unless you force it, and a refused push changes nothing on either side." },
    fetch: { path: ["remote", "repository"], text: "`fetch` downloads the commits you do not have and moves `origin/main` (and the other `origin/` names). It changes no branch of yours, no working file and nothing in the staging area." },
    pull: { path: ["repository", "index", "folder"], label: "pull = fetch + merge", text: "`pull` is a fetch, then a merge of `origin/main` into your branch (or a rebase, if you ask for one). When your branch has no commits of its own, the merge is a fast-forward: your branch slides forward, and the staging area and working folder update to match. When both sides have new commits, git fetches, then stops with an error that asks you to choose: `git pull --no-rebase` merges, `git pull --rebase` rebases." },
    clone: { path: ["remote", "repository", "index", "folder"], label: "clone (once)", text: "`clone` downloads every commit, branch and tag from GitHub, names that remote `origin` and records its branches as `origin/main` (and other `origin/` names), then makes your own `main` from `origin/main` and fills the staging area and the working folder." },
  };

  const COMMITS = ["commit-created", "merge-commit-created", "commit-replaced"];

  /* The order of a play, in ms: a lit arrow draws itself, then the work flies along it, one
     flight after another; the next group of flights leaves once the one before it has arrived.
     What a flight brings shows in each place as it gets there, and the commit graphs take their
     new state (their own motions) as the first commit lands. A flight passes its middle place
     halfway and arrives at AT.arrive of its run. */
  const EASE = "cubic-bezier(0.3, 0.7, 0.3, 1)";
  const TIMING = { arrow: 240, flight: { delay: 120, duration: 420 }, stagger: 80, land: 300, reveal: 160, pulse: 360 };
  const AT = { middle: 0.5, arrive: 0.88 };

  /* Commits reachable from `hash` in a snapshot: the commit and every ancestor it records. */
  function history(snapshot, hash) {
    const parents = new Map(snapshot.commits.map((commit) => [commit.hash, commit.parents]));
    const seen = new Set();
    const todo = hash ? [hash] : [];
    while (todo.length) {
      const next = todo.pop();
      if (parents.has(next) && !seen.has(next)) {
        seen.add(next);
        todo.push(...parents.get(next));
      }
    }
    return seen;
  }

  /* Whether your branch took in work from GitHub: it is the same branch, and its new tip reaches a
     remote-tracking branch's tip that its old tip did not (a fast-forward, a merge or a rebase). */
  function merged(before, after) {
    const now = history(after, after.head);
    const then = history(before, before.head);
    const reached = after.refs.some((ref) => ref.kind === "remote" && now.has(ref.target) && !then.has(ref.target));
    return Boolean(after.branch) && after.branch === before.branch && reached;
  }

  /* The commands that match a batch of feed events, in the order they run; [] when none does.
     `before` and `after` are your repository's snapshots around the batch. A pull lights the
     fetch arrow (when it fetched) and the pull arrow, its merge half, which also takes in the
     staging area's update and a merge commit, so neither lights add or commit. */
  function commands(events, before, after) {
    const has = (kind) => events.some((event) => event.kind === kind);
    const pushed = has("push-received");
    const pulled = !pushed && merged(before, after);
    const lit = [];
    if (has("repository-created") && after.refs.some((ref) => ref.kind === "remote")) lit.push("clone");
    if (has("file-staged") && !pulled) lit.push("add");
    if (COMMITS.some(has) && !pulled) lit.push("commit");
    if (pushed) lit.push("push");
    else if (has("remote-updated")) lit.push("fetch");
    if (pulled) lit.push("pull");
    return lit;
  }

  const hashes = (snapshot) => new Set(snapshot ? snapshot.commits.map((commit) => commit.hash) : []);
  /* Commits in `after` and not in `before`, oldest first (snapshots list them newest first). */
  const newCommits = (before, after) => after.commits.filter((commit) => !hashes(before).has(commit.hash)).map((commit) => commit.hash).reverse();

  /* Files whose content in `area` is new or different, and present there now. */
  function changedFiles(before, after, area) {
    const was = new Map(before.files.map((file) => [file.path, file[area]]));
    return after.files.filter((file) => file[area] !== null && was.get(file.path) !== file[area]).map((file) => file.path);
  }

  /* What travels along the lit arrows, in the order they run: [{what: "file" | "commit", id, by,
     path}], where `by` is the arrow and `path` the places the flight passes, first to last. Only
     commits that are on GitHub fly from GitHub; a commit made in your repository (a merge or
     rebase commit) does not fly, it appears there. */
  function flights(before, after, lit) {
    if (!before) return [];
    const fresh = newCommits(before.project, after.project);
    const onGithub = hashes(after.github);
    const fetched = lit.includes("fetch") || lit.includes("clone") ? fresh.filter((hash) => onGithub.has(hash)) : [];
    const made = fresh.filter((hash) => !fetched.includes(hash));
    const pushed = after.github ? newCommits(before.github, after.github) : [];
    const staged = changedFiles(before.project, after.project, "index");
    const checkedOut = changedFiles(before.project, after.project, "folder");
    const commit = (by, path) => (hash) => ({ what: "commit", id: hash, by, path });
    const file = (by, path) => (name) => ({ what: "file", id: name, by, path });
    const clone = ARROWS.clone.path;
    const plans = {
      add: () => staged.map(file("add", ARROWS.add.path)),
      commit: () => made.map(commit("commit", ARROWS.commit.path)),
      push: () => pushed.map(commit("push", ARROWS.push.path)),
      fetch: () => fetched.map(commit("fetch", ARROWS.fetch.path)),
      pull: () => checkedOut.map(file("pull", ARROWS.pull.path)),
      clone: () => [...fetched.map(commit("clone", clone.slice(0, 2))), ...checkedOut.map(file("clone", clone.slice(1)))],
    };
    return lit.flatMap((name) => plans[name]());
  }

  const { small } = TimeTheme;

  /* Text with `code` spans, as nodes. */
  const inline = (text) => text.split("`").map((part, index) => (index % 2 ? el("code", {}, part) : part));

  function fileRow(path, cell, states) {
    return el("li", { class: `tt-file state-${cell.state}`, "data-path": path },
      el("i", { class: "blob-dot", style: `--hue: ${RepoMap.blobHue(cell.blob || "000000")}`, "aria-hidden": "true" }),
      el("span", { class: "tt-file-name" }, path),
      cell.blob && el("code", { title: cell.blob }, cell.blob.slice(0, 7)),
      states[cell.state] && el("em", {}, states[cell.state]),
    );
  }

  function filePlace(area, files) {
    const rows = RepoMap.areaRows(files).filter((row) => row[area]);
    const { states } = RepoMap.DEFAULT_THEME.words;
    return el("section", { class: `tt-place is-${area}`, "data-area": area },
      el("h4", {}, PLACES[area]),
      rows.length ? el("ul", { class: "tt-files" }, rows.map((row) => fileRow(row.path, row[area], states))) : el("p", { class: "tt-place-empty" }, "No files."),
    );
  }

  function repositoryPlace(area, snapshot, showHead) {
    return el("section", { class: `tt-place is-${area}`, "data-area": area },
      el("h4", {}, PLACES[area]),
      snapshot ? el("div", { class: "tt-place-graph" }, RepoMap.render(snapshot, { theme: small, showHead })) : el("p", { class: "tt-place-empty" }, NO_REMOTE),
    );
  }

  const where = (area) => (area === "repository" ? "your repository" : `the ${PLACES[area].toLowerCase()}`);

  /* The route an arrow says aloud: "from A, through B and C, to D". */
  function route(path) {
    const [from, ...rest] = path;
    const to = rest.pop();
    const through = rest.length ? `, through ${rest.map(where).join(" and ")},` : "";
    return `from ${where(from)}${through} to ${where(to)}`;
  }

  /* An arrow with its Git word and a stop at each place it passes; `is-back` for the commands
     that bring work back from GitHub. */
  function arrow(name, lit) {
    const { path, label } = ARROWS[name];
    const order = Object.keys(PLACES);
    const backwards = order.indexOf(path.at(-1)) < order.indexOf(path[0]);
    const word = label || name;
    return el("div", { class: `tt-arrow is-${name}${backwards ? " is-back" : ""}${lit.includes(name) ? " is-active" : ""}`, "data-command": name, "aria-label": `${word}: ${route(path)}` },
      el("span", { class: "tt-arrow-label", "aria-hidden": "true" }, word),
      el("span", { class: "tt-arrow-shaft", "aria-hidden": "true" }),
      path.slice(1, -1).map((area) => el("span", { class: `tt-arrow-stop is-${area}`, "aria-hidden": "true" })),
    );
  }

  /* The sentences of the lit arrows; pull's tells its own fetch half. */
  const told = (lit) => (lit.includes("pull") ? lit.filter((name) => name !== "fetch") : lit);

  /* The four places as a figure, lighting `options.commands`' arrows and showing their sentences. */
  function render(observation, { commands: lit = [] } = {}) {
    const { project, github } = observation;
    return el("figure", { class: "tt-places", "aria-label": `The four places: ${Object.values(PLACES).join(", ")}` }, el("div", { class: "tt-places-grid" },
      el("div", { class: "tt-frame is-computer", "aria-hidden": "true" }, el("span", {}, COMPUTER)),
      el("div", { class: "tt-frame is-github", "aria-hidden": "true" }, el("span", {}, GITHUB)),
      filePlace("folder", project.files),
      arrow("add", lit),
      filePlace("index", project.files),
      arrow("commit", lit),
      repositoryPlace("repository", project, true),
      el("div", { class: "tt-arrows-pair" }, arrow("push", lit), arrow("fetch", lit)),
      repositoryPlace("remote", github, false),
      arrow("pull", lit),
      arrow("clone", lit),
    ), lit.length > 0 && el("figcaption", { class: "tt-places-caption" }, told(lit).map((name) => el("p", {}, inline(ARROWS[name].text)))));
  }

  const find = (scope, attribute, value) => [...scope.querySelectorAll(`[${attribute}]`)].find((node) => node.getAttribute(attribute) === value) || null;

  /* Where a flight starts or ends: the file's row or the commit's save point in that place; for
     files leaving your repository, the commit HEAD is on; else the place itself. */
  function spot(figure, area, flight) {
    const place = find(figure, "data-area", area);
    const exact = flight.what === "file" ? find(place, "data-path", flight.id) : find(place, "data-hash", flight.id);
    const point = exact && flight.what === "commit" ? exact.querySelector(".tt-save") : exact;
    const head = !point && area === "repository" ? place.querySelector(".map-commit.is-head .tt-save") : null;
    return point || head || place;
  }

  function centre(node, origin) {
    const box = node.getBoundingClientRect();
    return { x: box.left + box.width / 2 - origin.left, y: box.top + box.height / 2 - origin.top };
  }

  /* The point of the lit arrow nearest the middle of a flight, so the flight follows the arrow. */
  function via(shaft, from, to, origin) {
    const box = shaft.getBoundingClientRect();
    const clamp = (value, low, high) => Math.min(Math.max(value, low), high);
    return {
      x: clamp((from.x + to.x) / 2, box.left - origin.left, box.right - origin.left),
      y: clamp((from.y + to.y) / 2, box.top - origin.top, box.bottom - origin.top),
    };
  }

  /* What flies: a file by name with its content's colour, or a save point with its short hash. */
  function flyer(flight, after) {
    if (flight.what === "file") {
      const file = after.project.files.find((entry) => entry.path === flight.id);
      return el("div", { class: "tt-flyer is-file", "aria-hidden": "true" },
        el("i", { class: "blob-dot", style: `--hue: ${RepoMap.blobHue(file.folder || file.index || "000000")}` }), flight.id);
    }
    const commits = [...after.project.commits, ...(after.github ? after.github.commits : [])];
    const commit = commits.find((entry) => entry.hash === flight.id);
    return el("div", { class: "tt-flyer is-commit", "aria-hidden": "true" }, TimeTheme.mark("commit"), commit.short);
  }

  /* The commit graph of one place moves from its old drawing to its new one, `offset` ms late. */
  function settle(figure, area, before, after, showHead, offset, reduced) {
    const graph = find(figure, "data-area", area).querySelector(".repo-map");
    if (!graph || !before || !after) return [];
    const options = { theme: small, showHead };
    const motion = TimeMotion.motions(RepoMap.layout(before, options), RepoMap.layout(after, options), small.sizes);
    return TimeMotion.play(graph, motion, small, reduced, offset);
  }

  /* When each flight leaves: one after another within a group (same arrow, same kind of thing),
     and each group once the last flight of the one before has arrived. */
  function departures(trips) {
    const arrive = TIMING.flight.duration * AT.arrive;
    const delays = [];
    trips.forEach((flight, index) => {
      const previous = trips[index - 1];
      const together = previous && previous.by === flight.by && previous.what === flight.what;
      delays.push(index === 0 ? TIMING.flight.delay : delays[index - 1] + (together ? TIMING.stagger : arrive));
    });
    return delays;
  }

  /* Plays a transition {before, after, commands} on the figure render(after) drew; returns the
     animations started. */
  function play(figure, { before, after, commands: lit }, reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    if (reduced || !before || typeof figure.animate !== "function") return [];
    const started = [];
    const animate = (node, frames, timing) => {
      const animation = node.animate(frames, { easing: EASE, fill: "backwards", ...timing });
      started.push(animation);
      return animation;
    };
    const shaft = (name) => find(figure, "data-command", name).querySelector(".tt-arrow-shaft");
    const layer = el("div", { class: "tt-flights", "aria-hidden": "true" });
    figure.append(layer);
    const origin = figure.getBoundingClientRect();
    const trips = flights(before, after, lit);
    const delays = departures(trips);
    for (const name of lit) {
      const first = trips.findIndex((flight) => flight.by === name);
      animate(shaft(name), [{ transform: "scale(0)" }, { transform: "scale(1)" }], { duration: TIMING.arrow, delay: first > 0 ? delays[first] - TIMING.flight.delay : 0 });
    }
    const glow = "color-mix(in srgb, var(--map-head) 24%, transparent)";
    /* A file's row in `area` takes what the flight brings at `at` ms: a new row appears, a known
       row's content (its id and colour) changes, and the row glows once. */
    const reveal = (area, path, at) => {
      const row = find(find(figure, "data-area", area), "data-path", path);
      if (!row) return;
      const known = before.project.files.some((entry) => entry.path === path && entry[area] !== null);
      const parts = known ? [row.querySelector("code"), row.querySelector(".blob-dot")].filter(Boolean) : [row];
      for (const part of parts) animate(part, [{ opacity: 0, offset: 0 }], { delay: at, duration: TIMING.reveal });
      animate(row, [{ backgroundColor: "transparent" }, { backgroundColor: glow, offset: 0.2 }, { backgroundColor: "transparent" }], { delay: at, duration: TIMING.pulse, fill: "none" });
    };
    trips.forEach((flight, index) => {
      const delay = delays[index];
      const points = flight.path.map((area) => centre(spot(figure, area, flight), origin));
      const [from, to] = [points[0], points[points.length - 1]];
      const middle = points.length > 2 ? points[1] : via(shaft(flight.by), from, to, origin);
      const node = flyer(flight, after);
      node.style.left = `${from.x}px`;
      node.style.top = `${from.y}px`;
      layer.append(node);
      const at = (point) => `translate(-50%, -50%) translate(${point.x - from.x}px, ${point.y - from.y}px)`;
      /* Eased leg by leg, not as a whole, so the flyer is at each place at the time the place
         takes what it brings. */
      animate(node, [
        { transform: `${at(from)} scale(0.8)`, opacity: 0 },
        { transform: at(from), opacity: 1, offset: 0.12, easing: "ease-in-out" },
        { transform: at(middle), opacity: 1, offset: AT.middle, easing: "ease-in-out" },
        { transform: at(to), opacity: 1, offset: AT.arrive, easing: "linear" },
        { transform: at(to), opacity: 0 },
      ], { ...TIMING.flight, delay, easing: "linear", fill: "both" }).onfinish = () => node.remove();
      const stops = flight.what === "file" ? flight.path.slice(1) : [];
      stops.forEach((area, step) => reveal(area, flight.id, delay + TIMING.flight.duration * (step === stops.length - 1 ? AT.arrive : AT.middle)));
    });
    /* A graph moves as the first commit lands in it, or, for your origin/main after a push, as
       the commit lands on GitHub. */
    const firstCommit = (lands) => trips.findIndex((flight) => flight.what === "commit" && lands(flight));
    const landing = (area) => {
      const here = firstCommit((flight) => flight.path.at(-1) === area);
      const index = here >= 0 ? here : firstCommit(() => true);
      return index >= 0 ? delays[index] + TIMING.land : 0;
    };
    started.push(...settle(figure, "repository", before.project, after.project, true, landing("repository"), reduced));
    started.push(...settle(figure, "remote", before.github, after.github, false, landing("remote"), reduced));
    return started;
  }

  return { commands, flights, render, play, ARROWS, PLACES, TIMING };
})();
