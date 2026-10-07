"use strict";

/*
 * The level screen's four zones, side by side with drawn arrows between them: the workshop, the
 * cargo dock, the vault and the mothership, filled from each observation (zones.js). A zone that
 * does not exist yet (no repository, no GitHub) is drawn off, saying what switches it on. The
 * panel redraws only when what the zones hold changed; then the arrows of the git commands just
 * typed light up, a zone that switched on flashes, and what moved is shown moving (Zones.moves):
 * files and capsules fly from their old place to their new one, labels slide, a refused push
 * bounces off the mothership, capsules that left every branch fade off and those that came back
 * fade in; none of the movement plays when the player asked for reduced motion.
 * Needs dom.js, art-sprites.js, typed.js and zones.js. Defines one global, ZonePanel.
 */

/* global Dom, ArtSprites, Typed, Zones */
/* exported ZonePanel */

const ZonePanel = (function () {
  const { el, svg } = Dom;
  /* The graph's measures, in pixels: a lane's width, a capsule row's height, and where a
     capsule's block centre sits in its row (orbit.css draws the rows to match). */
  const LANE = 16;
  const ROW = 40;
  const CENTRE = 11;
  const ZONES = [
    { name: "workshop", title: "Workshop", git: "working folder" },
    { name: "dock", title: "Cargo dock", git: "staging area" },
    { name: "vault", title: "Vault", git: "local repository" },
    { name: "remote", title: "Mothership", git: "remote repository" },
  ];
  const FLOWS = [[["add", false]], [["commit", false]], [["push", false], ["pull", true]]];
  const LIT_MS = 1600;
  const FLY_MS = 720;
  const STATE_TAGS = { none: "", new: "new", edited: "edited", deleted: "deleted", staged: "on the dock", saved: "" };
  const STATE_TIPS = {
    none: "Git does not watch this folder",
    new: "untracked: Git does not follow it yet",
    edited: "modified: changed since it was last loaded",
    deleted: "deleted from the folder",
    staged: "its current version is on the dock",
    saved: "saved and unchanged",
  };
  const CHANGE_TAGS = { added: "new", modified: "change", deleted: "deleted", typechange: "type change" };
  const LEGEND = [["none", "no repository"], ["new", "new (untracked)"], ["edited", "edited (modified)"], ["staged", "on the dock (staged)"], ["saved", "saved (committed)"]];

  /* A sentence with commands in it: [text, [command], text, ...]. */
  const say = (...parts) => el("p", { class: "zone-empty" }, parts.map((part) => (Array.isArray(part) ? el("code", {}, part[0]) : part)));
  const OFF = {
    dock: () => say("Off. It switches on when you plant the flag with ", ["git init"], "."),
    vault: () => say("Off. Without a repository there is no history."),
    remote: () => say("Out of range: this mission has no mothership."),
  };
  const EMPTY = {
    workshop: () => say("Empty workshop. Create a file with ", ["touch"], "."),
    dock: () => say("Empty dock. Load changes with ", ["git add"], "."),
    vault: () => say("No capsules yet. Seal them with ", ["git commit"], "."),
    remote: () => say("Connected but empty. Launch your capsules with ", ["git push"], "."),
  };

  function fileChip(path, tag, attributes) {
    return el("span", { class: "file", ...attributes }, el("span", { class: "fname" }, path), tag && el("span", { class: "ftag" }, tag));
  }

  const capsule = (zone) => (commit) => el("div", { class: commit.parents.length > 1 ? "cap is-merge" : "cap", "data-key": `${zone}:${commit.hash}` },
    el("span", { class: "cgutter", "aria-hidden": "true" }, el("span", { class: "cblock", style: `margin-left:${commit.lane * LANE}px` })),
    el("div", { class: "cinfo" },
      el("div", { class: "cline" }, el("span", { class: "chash" }, commit.short), commit.labels.map((label) => el("span", { class: "ref", "data-kind": label.kind, "data-key": `${zone}-ref:${label.kind === "head" ? "HEAD" : label.text}` }, label.text))),
      el("span", { class: "cmsg", title: commit.subject }, commit.subject),
    ),
  );

  /* The line from a commit down to one of its parents (`row` its place in the list; a parent not
     in the list goes to the bottom). The first parent bends just above itself, so a branch
     splits off where it starts; another parent bends just below the merge, so a merge reaches
     out to the branch it joins. */
  function link(commit, row, parent, parentRow, first) {
    const x = commit.lane * LANE + 9;
    const y = row * ROW + CENTRE;
    const px = parent.lane * LANE + 9;
    const py = parentRow * ROW + CENTRE;
    const bend = first ? `L ${x} ${py - ROW} L ${px} ${py}` : `L ${px} ${y + ROW} L ${px} ${py}`;
    return svg("path", { class: "link", d: `M ${x} ${y} ${px === x ? `L ${px} ${py}` : bend}` });
  }

  /* The capsules as a graph: each in its lane, with lines from every commit to its parents. */
  function capsules(zone, commits) {
    const rows = new Map(commits.map((commit, index) => [commit.hash, index]));
    const width = (Math.max(...commits.map((commit) => commit.lane)) + 1) * LANE;
    const links = commits.flatMap((commit, row) => commit.parents.map((hash, index) => {
      const parentRow = rows.has(hash) ? rows.get(hash) : commits.length;
      const parent = rows.has(hash) ? commits[parentRow] : commit;
      return link(commit, row, parent, parentRow, index === 0);
    }));
    const lines = svg("svg", { class: "links", width, height: commits.length * ROW, "aria-hidden": "true" }, links);
    return el("div", { class: "caps", style: `--gutter:${width}px` }, lines, commits.map(capsule(zone)));
  }

  /* Each zone's items, or null when the zone is off. */
  function contents(zones) {
    const workshop = zones.workshop.map((file) => fileChip(file.path, STATE_TAGS[file.state], { "data-state": file.state, "data-key": `workshop:${file.path}`, title: STATE_TIPS[file.state] }));
    const dock = zones.dock && zones.dock.map((change) => fileChip(change.path, CHANGE_TAGS[change.change], { class: "file is-staged", "data-key": `dock:${change.path}` }));
    return {
      workshop: { count: workshop.length, nodes: workshop },
      dock: zones.dock && { count: dock.length, nodes: dock },
      vault: zones.vault && { count: zones.vault.length, nodes: zones.vault.length ? [capsules("vault", zones.vault)] : [] },
      remote: zones.remote && { count: zones.remote.length, nodes: zones.remote.length ? [capsules("remote", zones.remote)] : [] },
    };
  }

  function zoneShell({ name, title, git }) {
    const parts = { count: el("span", { class: "z-count" }, "–"), body: el("div", { class: "z-body" }) };
    parts.element = el("article", { class: "zone", "data-zone": name, "aria-label": title },
      el("header", { class: "z-head" }, el("span", { class: "zico", "aria-hidden": "true" }), el("div", {}, el("h3", {}, title), el("small", {}, git)), parts.count),
      parts.body,
    );
    return parts;
  }

  const flow = (arrows) => el("div", { class: "flow", "aria-hidden": "true" },
    arrows.map(([command, back]) => el("div", { class: back ? "fl is-back" : "fl", "data-arrow": command }, ArtSprites.icon("arrow"), el("span", {}, `git ${command}`))));

  /* Restarts a class's one-shot animation on a node, and takes the class off after `ms`. */
  function flash(node, name, ms, timers) {
    node.classList.remove(name);
    void node.offsetWidth;
    node.classList.add(name);
    timers.setTimeout(() => node.classList.remove(name), ms);
  }

  /* Each keyed item's place on the screen, before a redraw. */
  function places(element) {
    return new Map([...element.querySelectorAll("[data-key]")].map((node) => [node.dataset.key, { node, rect: node.getBoundingClientRect() }]));
  }

  /* A copy of the item that moved flies from where it was to where it is now; the item shows once
     the copy lands. */
  function fly(from, to, delay) {
    const target = to.getBoundingClientRect();
    if (!from.rect.width) return;
    const ghost = from.node.cloneNode(true);
    ghost.classList.add("ghost");
    Object.assign(ghost.style, { left: `${from.rect.left}px`, top: `${from.rect.top}px`, width: `${from.rect.width}px`, height: `${from.rect.height}px` });
    document.body.append(ghost);
    to.style.opacity = "0";
    const dx = target.left - from.rect.left;
    const dy = target.top - from.rect.top;
    const motion = ghost.animate([
      { transform: "translate(0, 0)", opacity: 1 },
      { transform: `translate(${dx * 0.5}px, ${dy * 0.5 - 40}px)`, opacity: 1, offset: 0.55 },
      { transform: `translate(${dx}px, ${dy}px)`, opacity: 0.4 },
    ], { duration: FLY_MS, delay, easing: "cubic-bezier(.45,0,.25,1)", fill: "both" });
    const land = () => {
      ghost.remove();
      to.style.opacity = "";
    };
    motion.finished.then(land, land);
  }

  /* A copy of an item that left every branch fades off from where it was. */
  function fade(from) {
    if (!from.rect.width) return;
    const ghost = from.node.cloneNode(true);
    ghost.classList.add("ghost");
    Object.assign(ghost.style, { left: `${from.rect.left}px`, top: `${from.rect.top}px`, width: `${from.rect.width}px`, height: `${from.rect.height}px` });
    document.body.append(ghost);
    const motion = ghost.animate([{ opacity: 1, transform: "translateX(0)" }, { opacity: 0, transform: "translateX(-24px)" }], { duration: FLY_MS, easing: "steps(6)", fill: "both" });
    motion.finished.then(() => ghost.remove(), () => ghost.remove());
  }

  /* An item that came back, or was made where it stands, fades in. */
  const appear = (node) => node.animate([{ opacity: 0, transform: "scale(.6)" }, { opacity: 1, transform: "scale(1.1)", offset: 0.7 }, { opacity: 1, transform: "scale(1)" }], { duration: 480, easing: "steps(4)" });

  /* An item thrown at a zone, which sends it back to where it is. */
  function bounce(node, zone) {
    const from = node.getBoundingClientRect();
    const at = zone.getBoundingClientRect();
    const dx = at.left + at.width / 2 - (from.left + from.width / 2);
    const dy = at.top + 30 - from.top;
    node.animate([
      { transform: "translate(0, 0)" },
      { transform: `translate(${dx * 0.85}px, ${dy * 0.85}px)`, offset: 0.45 },
      { transform: `translate(${dx * 0.7}px, ${dy * 0.7 - 16}px)`, offset: 0.55 },
      { transform: "translate(0, 0)" },
    ], { duration: 1100, easing: "cubic-bezier(.45,0,.25,1)" });
  }

  const find = (element, key) => [...element.querySelectorAll("[data-key]")].find((node) => node.dataset.key === key);

  /* Lights the arrows, wakes the zones and shows what moved. */
  function animate(element, shells, moves, before, { reducedMotion, timers }) {
    for (const command of moves.lit) flash(element.querySelector(`.fl[data-arrow="${command}"]`), "is-lit", LIT_MS, timers);
    for (const name of moves.wake) flash(shells[name].element, "is-waking", LIT_MS, timers);
    if (reducedMotion) return;
    moves.flights.forEach((flight, index) => {
      const from = before.get(flight.from);
      const to = find(element, flight.to);
      if (from && to) fly(from, to, index * 120);
    });
    for (const key of moves.fades) if (before.has(key)) fade(before.get(key));
    for (const key of moves.appears) if (find(element, key)) appear(find(element, key));
    for (const { from, to } of moves.bounces) if (find(element, from)) bounce(find(element, from), shells[to].element);
  }

  /* options: reducedMotion (no flying items; the arrows and zones still light), timers. */
  function create({ reducedMotion = true, timers = window } = {}) {
    const shells = Object.fromEntries(ZONES.map((zone) => [zone.name, zoneShell(zone)]));
    const row = el("div", { class: "viz-row" }, ZONES.map((zone, index) => [shells[zone.name].element, index < FLOWS.length && flow(FLOWS[index])]));
    const legend = el("ul", { class: "legend" }, LEGEND.map(([state, text]) => el("li", { "data-state": state }, text)));
    const element = el("section", { class: "viz px", "aria-label": "Your repository" }, row, legend);
    let drawn = null;
    let last = null;

    function draw(zones) {
      const filled = contents(zones);
      for (const { name } of ZONES) {
        const shell = shells[name];
        const zone = filled[name];
        shell.element.classList.toggle("is-dormant", !zone);
        shell.count.textContent = zone ? String(zone.count) : "–";
        shell.body.replaceChildren(...(!zone ? [OFF[name]()] : zone.count ? zone.nodes : [EMPTY[name]()]));
      }
    }

    return {
      element,

      update(observation) {
        const zones = Zones.read(observation);
        const text = JSON.stringify(zones);
        const before = places(element);
        const moves = last && Zones.moves(last, zones, Typed.gitCommands(observation.commands), Typed.failedGitCommands(observation.commands));
        last = zones;
        if (text !== drawn) draw(zones);
        drawn = text;
        if (moves) animate(element, shells, moves, before, { reducedMotion, timers });
      },
    };
  }

  return { create };
})();
