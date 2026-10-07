"use strict";

/*
 * The level screen's four zones, side by side with drawn arrows between them: the workshop, the
 * cargo dock, the vault and the mothership, filled from each observation (zones.js). A zone that
 * does not exist yet (no repository, no GitHub) is drawn off, saying what switches it on. The
 * panel redraws only when what the zones hold changed; then the arrows of the git commands just
 * typed light up, a zone that switched on flashes, and the files and capsules that moved fly from
 * their old place to their new one (Zones.moves), unless the player asked for reduced motion.
 * Needs dom.js, art-sprites.js, typed.js and zones.js. Defines one global, ZonePanel.
 */

/* global Dom, ArtSprites, Typed, Zones */
/* exported ZonePanel */

const ZonePanel = (function () {
  const { el } = Dom;
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

  const capsule = (zone) => (commit) => el("div", { class: "cap", "data-key": `${zone}:${commit.hash}` },
    el("span", { class: "cblock", "aria-hidden": "true" }),
    el("div", { class: "cinfo" },
      el("div", { class: "cline" }, el("span", { class: "chash" }, commit.short), commit.labels.map((label) => el("span", { class: "ref", "data-kind": label.kind }, label.text))),
      el("span", { class: "cmsg", title: commit.subject }, commit.subject),
    ),
  );

  const capsules = (zone, commits) => el("div", { class: "caps" }, commits.map(capsule(zone)));

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

  /* Lights the arrows, wakes the zones and flies what moved. */
  function animate(element, shells, moves, before, { reducedMotion, timers }) {
    for (const command of moves.lit) flash(element.querySelector(`.fl[data-arrow="${command}"]`), "is-lit", LIT_MS, timers);
    for (const name of moves.wake) flash(shells[name].element, "is-waking", LIT_MS, timers);
    if (reducedMotion) return;
    moves.flights.forEach((flight, index) => {
      const from = before.get(flight.from);
      const to = [...element.querySelectorAll("[data-key]")].find((node) => node.dataset.key === flight.to);
      if (from && to) fly(from, to, index * 120);
    });
  }

  /* options: reducedMotion (no flying items; the arrows and zones still light), timers. */
  function create({ reducedMotion = true, timers = window } = {}) {
    const shells = Object.fromEntries(ZONES.map((zone) => [zone.name, zoneShell(zone)]));
    const row = el("div", { class: "viz-row" }, ZONES.map((zone, index) => [shells[zone.name].element, index < FLOWS.length && flow(FLOWS[index])]));
    const legend = el("ul", { class: "legend" }, LEGEND.map(([state, text]) => el("li", { "data-state": state }, text)));
    const element = el("section", { class: "viz px", "aria-label": "Your repository" }, row, legend);
    let drawn = null;
    let last = null;

    return {
      element,

      update(observation) {
        const zones = Zones.read(observation);
        const text = JSON.stringify(zones);
        if (text === drawn) return;
        drawn = text;
        const before = places(element);
        const moves = last && Zones.moves(last, zones, Typed.gitCommands(observation.commands));
        last = zones;
        const filled = contents(zones);
        for (const { name } of ZONES) {
          const shell = shells[name];
          const zone = filled[name];
          shell.element.classList.toggle("is-dormant", !zone);
          shell.count.textContent = zone ? String(zone.count) : "–";
          shell.body.replaceChildren(...(!zone ? [OFF[name]()] : zone.count ? zone.nodes : [EMPTY[name]()]));
        }
        if (moves) animate(element, shells, moves, before, { reducedMotion, timers });
      },
    };
  }

  return { create };
})();
