"use strict";

/*
 * The four places: your computer (working folder, staging area, your repository) next to
 * GitHub (the remote repository), with an arrow for each command that moves work between them:
 * add, commit, push, fetch, pull and clone. Files are pages, each with its name and the short id
 * of its content (its blob id), so a changed copy shows a different id. The staging area is an
 * open box: the next commit, holding every tracked file. A commit is a closed box on its
 * timeline, labelled with its short hash. Everything drawn is the player's own: the pages of the
 * three areas with git status's words (RepoMap.areaRows, the rule the three areas strip uses)
 * and the two commit graphs, drawn by the map renderer with closed boxes, origin/main included.
 *
 * commands(events, before, after) says which arrows match what just happened, from the feed's
 * own event kinds and your repository's two snapshots; flights(before, after, commands) says
 * what travels along them: the files and commits that really changed place between the two
 * observations. Both are pure. render(...) draws the figure, lights those arrows and shows their
 * sentences; play(...) runs the flights (a page's copy, or a box that closes as it leaves the
 * staging area) and the commit graphs' own motions (theme-time-motion.js). Every sentence is
 * checked against git 2.43 (docs-draft/four-places.md). Needs dom.js, map.js, theme-time.js and
 * theme-time-motion.js. Defines one global, TimePlaces.
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
  /* What the boxes are, under the titles of the places that hold them. */
  const NOTES = { index: "open box: the next commit", repository: "closed boxes: the commits" };
  const COMPUTER = "Your computer";
  const GITHUB = "GitHub (the practice copy)";
  const NO_REMOTE = "No remote yet.";
  const NO_FILES = "No files.";

  /* Each command's arrow: the places its work passes, first to last, and the checked sentence
     shown when it lights (A1 to A6). The pull arrow is pull's merge half: its fetch half is the
     fetch arrow (`after`), which lights with it and which its spoken route names first. */
  const ARROWS = {
    add: { path: ["folder", "index"], text: "`add` copies a file's current content from the working folder into the staging area; the working folder keeps it." },
    commit: { path: ["index", "repository"], text: "`commit` saves the staging area as a new commit in your repository; the staging area keeps its files. Your branch moves onto the new commit, and `origin/main` does not move." },
    push: { path: ["repository", "remote"], text: "`push` sends the commits GitHub is missing and moves GitHub's branch to your commit; your `origin/main` moves to match. Git refuses a push that is not a fast-forward unless you force it, and a refused push changes nothing on either side." },
    fetch: { path: ["remote", "repository"], text: "`fetch` downloads the commits you do not have and moves `origin/main` (and the other `origin/` names). It changes no branch of yours, no working file and nothing in the staging area." },
    pull: { path: ["repository", "index", "folder"], label: "pull = fetch + merge", after: "fetch", text: "`pull` is a fetch, then a merge of `origin/main` into your branch (or a rebase, if you ask for one). When your branch has no commits of its own, the merge is a fast-forward: your branch slides forward, and the staging area and working folder update to match. When both sides have new commits, git fetches, then stops with an error that asks you to choose: `git pull --no-rebase` merges, `git pull --rebase` rebases." },
    clone: { path: ["remote", "repository", "index", "folder"], label: "clone (once)", text: "`clone` downloads every commit, branch and tag from GitHub, names that remote `origin` and records its branches as `origin/main` (and other `origin/` names), then makes your own `main` from `origin/main` and fills the staging area and the working folder." },
  };

  const COMMITS = ["commit-created", "merge-commit-created", "commit-replaced"];

  /* The order of a play, in ms: a lit arrow draws itself, then the work flies along it, one
     flight after another; the next group of flights leaves once the one before it has arrived.
     What a flight brings shows in each place as it gets there, and the commit graphs take their
     new state (their own motions) as the first commit lands. A flight passes its middle place
     halfway and arrives at AT.arrive of its run. */
  const EASE = "cubic-bezier(0.3, 0.7, 0.3, 1)";
  const TIMING = { arrow: 300, flight: { delay: 150, duration: 520 }, stagger: 100, spread: 300, land: 380, reveal: 200, pulse: 450 };
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

  /* Whether your branch took in work from GitHub: it is the same branch, its new tip reaches the
     tip of its upstream, origin/<branch> (as clone and push -u set it), which its old tip did not,
     and it kept its own commits (a fast-forward or a merge) or replayed them on top (a rebase).
     A branch that now sits exactly on its upstream without its old tip was reset there, as by
     git reset --hard origin/main. A reset of a branch with no commits of its own looks the same as
     a fast-forward, and lights pull. */
  function merged(before, after) {
    const upstream = after.refs.find((ref) => ref.kind === "remote" && ref.name === `origin/${after.branch}`);
    if (!after.branch || after.branch !== before.branch || !upstream) return false;
    const now = history(after, after.head);
    const reached = now.has(upstream.target) && !history(before, before.head).has(upstream.target);
    const kept = !before.head || now.has(before.head) || after.head !== upstream.target;
    return reached && kept;
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

  const { boxes } = TimeTheme;

  /* Text with `code` spans, as nodes. */
  const inline = (text) => text.split("`").map((part, index) => (index % 2 ? el("code", {}, part) : part));

  /* A page's picture, coloured by its content (the same content always looks the same). */
  const pageIcon = (blob) => el("span", { class: "tt-page-icon", style: blob ? `--hue: ${RepoMap.blobHue(blob)}` : null, "aria-hidden": "true" });

  /* A file as a page: its content's colour, its name, the short id of its content (the blob id)
     and the change git status lists for it in this place. A file git says is deleted here is the
     gap its page left. */
  function page(path, cell, said) {
    return el("li", { class: `tt-page${cell.blob ? "" : " is-missing"}`, "data-path": path, "data-change": cell.change },
      pageIcon(cell.blob),
      el("span", { class: "tt-page-name" }, path),
      cell.blob && el("code", { class: "tt-page-id", title: cell.blob }, cell.blob.slice(0, 7)),
      cell.change && el("em", {}, said[cell.change]),
    );
  }

  /* A place's title and note; a repository on `owner`'s computer is `owner`'s, not yours. */
  function title(area, owner = null) {
    const name = owner && area === "repository" ? `${owner}'s repository` : PLACES[area];
    return [el("h4", {}, name), NOTES[area] && el("p", { class: "tt-place-note" }, NOTES[area])];
  }

  /* The working folder's pages, or the staging area's: an open box holding the next commit. */
  function filePlace(area, files, owner = null) {
    const rows = RepoMap.areaRows(files).filter((row) => row[area]);
    const said = boxes.words.states[area];
    const pages = rows.length ? el("ul", { class: "tt-pages" }, rows.map((row) => page(row.path, row[area], said))) : el("p", { class: "tt-place-empty" }, NO_FILES);
    const held = area === "index"
      ? el("div", { class: "tt-open-box" }, el("span", { class: "tt-flap is-left", "aria-hidden": "true" }), el("span", { class: "tt-flap is-right", "aria-hidden": "true" }), pages)
      : pages;
    return el("section", { class: `tt-place is-${area}`, "data-area": area }, title(area, owner), held);
  }

  /* A repository's commits: closed boxes on its timeline. GitHub has no HEAD you are on, so an
     empty GitHub only says it has no commits. */
  function repositoryPlace(area, snapshot, showHead, owner = null) {
    const empty = !snapshot ? NO_REMOTE : !showHead && !snapshot.commits.length ? boxes.words.noCommits : null;
    return el("section", { class: `tt-place is-${area}`, "data-area": area },
      title(area, owner),
      empty ? el("p", { class: "tt-place-empty" }, empty) : el("div", { class: "tt-place-graph" }, RepoMap.render(snapshot, { theme: boxes, showHead })),
    );
  }

  const NOUNS = { folder: "working folder", index: "staging area", repository: "repository", remote: "remote repository" };

  /* A place as said aloud: yours, unless `owner` names whose computer it is on. */
  function where(area, owner) {
    let said = area === "repository" ? "your repository" : `the ${NOUNS[area]}`;
    if (owner && area !== "remote") said = `${owner}'s ${NOUNS[area]}`;
    return said;
  }

  /* The route an arrow says aloud: "from A, through B and C, to D". */
  function route(path, owner) {
    const [from, ...rest] = path;
    const to = rest.pop();
    const through = rest.length ? `, through ${rest.map((area) => where(area, owner)).join(" and ")},` : "";
    return `from ${where(from, owner)}${through} to ${where(to, owner)}`;
  }

  /* An arrow with its Git word, from the first place of `part` to its last: the whole route, or
     one leg of it for an arrow drawn in parts (pull's merge half runs beside commit, then add),
     which shows only the command's name. Only the first part says the route aloud, naming
     `owner`'s places when the computer is someone else's. A whole arrow has a stop at each place
     it passes; `is-back` marks the legs that bring work back from GitHub. */
  function arrow(name, lit, part = ARROWS[name].path, owner = null) {
    const { path, label, after } = ARROWS[name];
    const order = Object.keys(PLACES);
    const backwards = order.indexOf(part.at(-1)) < order.indexOf(part[0]);
    const word = label || name;
    const whole = part === path;
    const first = after ? `the ${after} arrow, then ` : "";
    const spoken = part[0] === path[0] ? { "aria-label": `${word}: ${first}${route(path, owner)}` } : { "aria-hidden": "true" };
    return el("div", { class: `tt-arrow is-${name}${backwards ? " is-back" : ""}${lit.includes(name) ? " is-active" : ""}`, "data-command": name, ...spoken },
      el("span", { class: "tt-arrow-label", "aria-hidden": "true" }, whole ? word : name),
      el("span", { class: "tt-arrow-shaft", "aria-hidden": "true" }),
      whole && path.slice(1, -1).map((area) => el("span", { class: `tt-arrow-stop is-${area}`, "aria-hidden": "true" })),
    );
  }

  /* Two arrows across one gap between places: the one towards GitHub above, the one back below. */
  const pair = (gap, ...arrows) => el("div", { class: `tt-arrows-pair is-gap-${gap}` }, arrows);

  /* The sentences of the lit arrows; pull's tells its own fetch half. */
  const told = (lit) => (lit.includes("pull") ? lit.filter((name) => name !== "fetch") : lit);

  /* The four places as a figure, lighting `options.commands`' arrows and showing their sentences. */
  function render(observation, { commands: lit = [] } = {}) {
    const { project, github } = observation;
    const merge = ARROWS.pull.path;
    return el("figure", { class: "tt-places", "aria-label": `The four places: ${Object.values(PLACES).join(", ")}` }, el("div", { class: "tt-places-grid" },
      el("div", { class: "tt-frame is-computer", "aria-hidden": "true" }, el("span", {}, COMPUTER)),
      el("div", { class: "tt-frame is-github", "aria-hidden": "true" }, el("span", {}, GITHUB)),
      filePlace("folder", project.files),
      pair(1, arrow("add", lit), arrow("pull", lit, merge.slice(1))),
      filePlace("index", project.files),
      pair(2, arrow("commit", lit), arrow("pull", lit, merge.slice(0, 2))),
      repositoryPlace("repository", project, true),
      pair(3, arrow("push", lit), arrow("fetch", lit)),
      repositoryPlace("remote", github, false),
      arrow("clone", lit),
    ), lit.length > 0 && el("figcaption", { class: "tt-places-caption" }, told(lit).map((name) => el("p", {}, inline(ARROWS[name].text)))));
  }

  const find = (scope, attribute, value) => [...scope.querySelectorAll(`[${attribute}]`)].find((node) => node.getAttribute(attribute) === value) || null;

  /* Where play finds each place and each command's arrows: in the figure itself, unless the
     caller (a figure with more than one computer) says. */
  const within = (figure) => ({
    place: (area) => find(figure, "data-area", area),
    arrows: (name) => [...figure.querySelectorAll(".tt-arrow")].filter((node) => node.getAttribute("data-command") === name),
  });

  /* Where a flight starts or ends: the file's page or the commit's box in that place; for files
     leaving your repository, the box HEAD is on; for a commit leaving the staging area, its open
     box; else the place itself. */
  function spot(lookup, area, flight) {
    const place = lookup.place(area);
    const exact = flight.what === "file" ? find(place, "data-path", flight.id) : find(place, "data-hash", flight.id);
    const point = exact && flight.what === "commit" ? exact.querySelector(".tt-save") : exact;
    const head = !point && area === "repository" ? place.querySelector(".map-commit.is-head .tt-save") : null;
    const open = !point && flight.what === "commit" ? place.querySelector(".tt-open-box") : null;
    return point || head || open || place;
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

  /* What flies: a copy of a file's page, by name and content's colour; or a closed box with its
     short hash on the label. A commit made now leaves the staging area as a copy of the open box,
     still open, holding a page for every tracked file, and closes on the way. */
  function flyer(flight, after) {
    if (flight.what === "file") {
      const file = after.project.files.find((entry) => entry.path === flight.id);
      return el("div", { class: "tt-flyer is-file", "aria-hidden": "true" }, pageIcon(file.folder || file.index), flight.id);
    }
    const commits = [...after.project.commits, ...(after.github ? after.github.commits : [])];
    const commit = commits.find((entry) => entry.hash === flight.id);
    const made = flight.by === "commit";
    const packed = made ? after.project.files.filter((file) => file.head !== null) : [];
    return el("div", { class: `tt-flyer is-commit${made ? " is-closing" : ""}`, "aria-hidden": "true" },
      el("span", { class: "tt-box-icon" },
        made && [el("span", { class: "tt-flap is-left" }), el("span", { class: "tt-flap is-right" })],
        packed.length > 0 && el("span", { class: "tt-flyer-pages" }, packed.map((file) => pageIcon(file.head))),
      ),
      commit.short,
    );
  }

  /* The commit graph of one place moves from its old drawing to its new one, `offset` ms late. */
  function settle(place, before, after, showHead, offset, reduced) {
    const graph = place.querySelector(".repo-map");
    if (!graph || !before || !after) return [];
    return TimeMotion.playMap(graph, before, after, { theme: boxes, showHead, reduced, offset });
  }

  /* When each flight leaves: one after another within a group (same arrow, same kind of thing),
     spread over at most TIMING.spread however many there are, and each group once the last flight
     of the one before has arrived. */
  function departures(trips) {
    const arrive = TIMING.flight.duration * AT.arrive;
    const alike = (one, other) => one.by === other.by && one.what === other.what;
    const delays = [];
    trips.forEach((flight, index) => {
      const previous = trips[index - 1];
      const group = trips.filter((other) => alike(other, flight)).length;
      const stagger = Math.min(TIMING.stagger, TIMING.spread / Math.max(group - 1, 1));
      delays.push(index === 0 ? TIMING.flight.delay : delays[index - 1] + (alike(previous, flight) ? stagger : arrive));
    });
    return delays;
  }

  /* Plays a transition {before, after, commands} on the figure render(after) drew; returns the
     animations started. `lookup` finds the places and arrows (see `within`). */
  function play(figure, { before, after, commands: lit }, reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches, lookup = within(figure)) {
    if (reduced || !before || typeof figure.animate !== "function") return [];
    const started = [];
    const animate = (node, frames, timing) => {
      const animation = node.animate(frames, { easing: EASE, fill: "backwards", ...timing });
      started.push(animation);
      return animation;
    };
    const shafts = (name) => lookup.arrows(name).map((node) => node.querySelector(".tt-arrow-shaft"));
    const layer = el("div", { class: "tt-flights", "aria-hidden": "true" });
    figure.append(layer);
    const origin = figure.getBoundingClientRect();
    const trips = flights(before, after, lit);
    const delays = departures(trips);
    for (const name of lit) {
      const first = trips.findIndex((flight) => flight.by === name);
      for (const shaft of shafts(name)) animate(shaft, [{ transform: "scale(0)" }, { transform: "scale(1)" }], { duration: TIMING.arrow, delay: first > 0 ? delays[first] - TIMING.flight.delay : 0 });
    }
    const glow = "color-mix(in srgb, var(--map-head) 24%, transparent)";
    /* A file's page in `area` takes what the flight brings at `at` ms: a new page appears; a known
       page's old id and colour fade out as the new ones, and git's words for them, fade in; and the
       page glows once. */
    const reveal = (area, path, at) => {
      const row = find(lookup.place(area), "data-path", path);
      if (!row) return;
      const was = before.project.files.find((entry) => entry.path === path);
      const old = was ? was[area] : null;
      if (old) {
        const gone = el("span", { class: "tt-page-was", "aria-hidden": "true" }, pageIcon(old), el("code", { class: "tt-page-id" }, old.slice(0, 7)));
        row.append(gone);
        animate(gone, [{ opacity: 1 }, { opacity: 0 }], { delay: at, duration: TIMING.reveal, fill: "both" }).onfinish = () => gone.remove();
      }
      const parts = old ? [row.querySelector("code.tt-page-id"), row.querySelector(".tt-page-icon"), row.querySelector("em")].filter(Boolean) : [row];
      for (const part of parts) animate(part, [{ opacity: 0, offset: 0 }], { delay: at, duration: TIMING.reveal });
      animate(row, [{ backgroundColor: "transparent" }, { backgroundColor: glow, offset: 0.2 }, { backgroundColor: "transparent" }], { delay: at, duration: TIMING.pulse, fill: "none" });
    };
    trips.forEach((flight, index) => {
      const delay = delays[index];
      const points = flight.path.map((area) => centre(spot(lookup, area, flight), origin));
      const [from, to] = [points[0], points[points.length - 1]];
      const middle = points.length > 2 ? points[1] : via(shafts(flight.by)[0], from, to, origin);
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
      node.querySelectorAll(".tt-flap").forEach((flap, side) => {
        animate(flap, [{ transform: `rotate(${side ? 125 : -125}deg)` }, { transform: "rotate(0deg)" }], { delay: delay + TIMING.flight.duration * 0.12, duration: TIMING.flight.duration * 0.3, fill: "both" });
      });
      const stops = flight.what === "file" ? flight.path.slice(1) : [];
      stops.forEach((area, step) => reveal(area, flight.id, delay + TIMING.flight.duration * (step === stops.length - 1 ? AT.arrive : AT.middle)));
    });
    /* Pages changed in the working folder that no flight brought (the player edited or made
       them) change where they lie. */
    const brought = new Set(trips.filter((flight) => flight.what === "file").map((flight) => flight.id));
    for (const path of changedFiles(before.project, after.project, "folder").filter((name) => !brought.has(name))) reveal("folder", path, TIMING.flight.delay);
    /* A graph moves as the first commit lands in it, or, for your origin/main after a push, as
       the commit lands on GitHub. */
    const firstCommit = (lands) => trips.findIndex((flight) => flight.what === "commit" && lands(flight));
    const landing = (area) => {
      const here = firstCommit((flight) => flight.path.at(-1) === area);
      const index = here >= 0 ? here : firstCommit(() => true);
      return index >= 0 ? delays[index] + TIMING.land : 0;
    };
    started.push(...settle(lookup.place("repository"), before.project, after.project, true, landing("repository"), reduced));
    started.push(...settle(lookup.place("remote"), before.github, after.github, false, landing("remote"), reduced));
    return started;
  }

  /* The figure's building blocks, for figures with more than one computer (theme-time-share.js). */
  const parts = { filePlace, repositoryPlace, arrow, pair, inline };

  return { commands, flights, render, play, parts, ARROWS, PLACES, TIMING };
})();
