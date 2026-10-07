"use strict";

/*
 * The level screen's four zones, side by side with drawn arrows between them: the workshop, the
 * cargo dock, the vault and the mothership, filled from each observation (zones.js). A zone that
 * does not exist yet (no repository, no GitHub) is drawn off, saying what switches it on. The
 * panel redraws only when what the zones hold changed. Needs dom.js, art-sprites.js and
 * zones.js. Defines one global, ZonePanel.
 */

/* global Dom, ArtSprites, Zones */
/* exported ZonePanel */

const ZonePanel = (function () {
  const { el } = Dom;
  const ZONES = [
    { name: "workshop", title: "Workshop", git: "working folder" },
    { name: "dock", title: "Cargo dock", git: "staging area" },
    { name: "vault", title: "Vault", git: "local repository" },
    { name: "remote", title: "Mothership", git: "remote repository" },
  ];
  const FLOWS = [[["git add", false]], [["git commit", false]], [["git push", false], ["git pull", true]]];
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

  const capsule = (commit) => el("div", { class: "cap" },
    el("span", { class: "cblock", "aria-hidden": "true" }),
    el("div", { class: "cinfo" },
      el("div", { class: "cline" }, el("span", { class: "chash" }, commit.short), commit.labels.map((label) => el("span", { class: "ref", "data-kind": label.kind }, label.text))),
      el("span", { class: "cmsg", title: commit.subject }, commit.subject),
    ),
  );

  const capsules = (commits) => el("div", { class: "caps" }, commits.map(capsule));

  /* Each zone's items, or null when the zone is off. */
  function contents(zones) {
    const workshop = zones.workshop.map((file) => fileChip(file.path, STATE_TAGS[file.state], { "data-state": file.state, title: STATE_TIPS[file.state] }));
    const dock = zones.dock && zones.dock.map((change) => fileChip(change.path, CHANGE_TAGS[change.change], { class: "file is-staged" }));
    return {
      workshop: { count: workshop.length, nodes: workshop },
      dock: zones.dock && { count: dock.length, nodes: dock },
      vault: zones.vault && { count: zones.vault.length, nodes: zones.vault.length ? [capsules(zones.vault)] : [] },
      remote: zones.remote && { count: zones.remote.length, nodes: zones.remote.length ? [capsules(zones.remote)] : [] },
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
    arrows.map(([label, back]) => el("div", { class: back ? "fl is-back" : "fl" }, ArtSprites.icon("arrow"), el("span", {}, label))));

  function create() {
    const shells = Object.fromEntries(ZONES.map((zone) => [zone.name, zoneShell(zone)]));
    const row = el("div", { class: "viz-row" }, ZONES.map((zone, index) => [shells[zone.name].element, index < FLOWS.length && flow(FLOWS[index])]));
    const legend = el("ul", { class: "legend" }, LEGEND.map(([state, text]) => el("li", { "data-state": state }, text)));
    const element = el("section", { class: "viz px", "aria-label": "Your repository" }, row, legend);
    let drawn = null;

    return {
      element,

      update(observation) {
        const zones = Zones.read(observation);
        const text = JSON.stringify(zones);
        if (text === drawn) return;
        drawn = text;
        const filled = contents(zones);
        for (const { name } of ZONES) {
          const shell = shells[name];
          const zone = filled[name];
          shell.element.classList.toggle("is-dormant", !zone);
          shell.count.textContent = zone ? String(zone.count) : "–";
          shell.body.replaceChildren(...(!zone ? [OFF[name]()] : zone.count ? zone.nodes : [EMPTY[name]()]));
        }
      },
    };
  }

  return { create };
})();
