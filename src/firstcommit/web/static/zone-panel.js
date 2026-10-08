"use strict";

/*
 * The level screen's four zones, side by side with drawn arrows between them: the workshop, the
 * cargo dock, the vault and the mothership, filled from each observation (zones.js). A zone that
 * does not exist yet (no repository, no GitHub) is drawn off, saying what switches it on. The
 * panel redraws only when what the zones hold changed; then the arrows of the git commands just
 * typed light up, a zone that switched on flashes, and what moved is shown moving (Zones.moves):
 * files and capsules fly from their old place to their new one, labels slide, a refused push
 * bounces off the mothership, capsules that left every branch fade off and those that came back
 * fade in; none of the movement plays when the player asked for reduced motion. In a level with a
 * teammate the zones become two stations, yours and Alex's (each a workshop, a dock and a vault),
 * with the mothership above and between them, and capsules fly between the stations through it.
 * Needs dom.js, strings.js, art-sprites.js, typed.js and zones.js. Defines one global, ZonePanel.
 */

/* global Dom, Strings, ArtSprites, Typed, Zones */
/* exported ZonePanel */

const ZonePanel = (function () {
  const { el, svg } = Dom;
  const { t, parts } = Strings;
  /* The graph's measures, in pixels: a lane's width, a capsule row's height, and where a
     capsule's block centre sits in its row (orbit.css draws the rows to match). */
  const LANE = 16;
  const ROW = 40;
  const CREW_ROW = 72;
  const SHOWN_LABELS = 2;
  const CENTRE = 11;
  const ZONES = ["workshop", "dock", "vault", "remote"];
  const STATION = ["workshop", "dock", "vault"];
  const CREW = STATION.map((name) => `crew-${name}`);
  const base = (key) => key.replace(/^crew-/, "");
  const FLOWS = [[["add", false]], [["commit", false]], [["push", false], ["pull", true]]];
  const LIT_MS = 1600;
  const FLY_MS = 720;
  const CRACK_MS = 600;
  const RISE_MS = 800;
  const TAGGED = ["conflicted", "new", "edited", "deleted", "staged"];
  const LEGEND = ["none", "conflicted", "new", "edited", "staged", "saved"];
  const stateTag = (state) => (TAGGED.includes(state) ? t(`zones.tag.${state}`) : "");

  /* A sentence from the strings, its commands as code. */
  const say = (key) => el("p", { class: "zone-empty" }, parts(key).map((part) => (typeof part === "string" ? part : el("code", {}, part.code))));
  const OFF = { dock: "zones.off.dock", vault: "zones.off.vault", remote: "zones.off.remote" };
  const EMPTY = { workshop: "zones.empty.workshop", dock: "zones.empty.dock", vault: "zones.empty.vault", remote: "zones.empty.remote" };

  function fileChip(path, tag, attributes) {
    const conflicted = attributes["data-state"] === "conflicted";
    return el("span", { class: "file", ...attributes }, conflicted && ArtSprites.icon("conflict"), el("span", { class: "fname" }, path), tag && el("span", { class: "ftag" }, tag));
  }

  /* A revert capsule's block is the capsule turned upside down. */
  const block = (commit) => (commit.revert
    ? el("span", { class: "cblock is-revert", style: `margin-left:${commit.lane * LANE}px` }, ArtSprites.icon("inverted"))
    : el("span", { class: "cblock", style: `margin-left:${commit.lane * LANE}px` }));

  /* A capsule's labels: the first few as they are, the rest folded into a count that names them,
     so a busy commit never outgrows its row. */
  function labelChips(zone, labels) {
    const folded = labels.slice(SHOWN_LABELS);
    return [
      labels.slice(0, SHOWN_LABELS).map((label) => el("span", { class: "ref", "data-kind": label.kind, "data-key": `${zone}-ref:${label.kind === "head" ? "HEAD" : label.text}` }, label.text)),
      folded.length > 0 && el("span", { class: "ref ref-more", title: folded.map((label) => label.text).join(", ") }, `+${folded.length}`),
    ];
  }

  const capsule = (zone) => (commit) => el("div", { class: commit.parents.length > 1 ? "cap is-merge" : "cap", "data-key": `${zone}:${commit.hash}` },
    el("span", { class: "cgutter", "aria-hidden": "true" }, block(commit)),
    el("div", { class: "cinfo" },
      el("div", { class: "cline" }, el("span", { class: "chash" }, commit.short), labelChips(zone, commit.labels)),
      el("span", { class: "cmsg", title: commit.subject }, commit.subject),
    ),
  );

  /* The line from a commit down to one of its parents (`row` its place in the list, `height` a
     row's height; a parent not in the list goes to the bottom). The first parent bends just above itself, so a branch
     splits off where it starts; another parent bends just below the merge, so a merge reaches
     out to the branch it joins. */
  function link(commit, row, parent, parentRow, first, height) {
    const x = commit.lane * LANE + 9;
    const y = row * height + CENTRE;
    const px = parent.lane * LANE + 9;
    const py = parentRow * height + CENTRE;
    const bend = first ? `L ${x} ${py - height} L ${px} ${py}` : `L ${px} ${y + height} L ${px} ${py}`;
    return svg("path", { class: "link", d: `M ${x} ${y} ${px === x ? `L ${px} ${py}` : bend}` });
  }

  /* The capsules as a graph: each in its lane, `height` pixels a row, with lines from every
     commit to its parents. */
  function capsules(zone, commits, height) {
    const rows = new Map(commits.map((commit, index) => [commit.hash, index]));
    const width = (Math.max(...commits.map((commit) => commit.lane)) + 1) * LANE;
    const links = commits.flatMap((commit, row) => commit.parents.map((hash, index) => {
      const parentRow = rows.has(hash) ? rows.get(hash) : commits.length;
      const parent = rows.has(hash) ? commits[parentRow] : commit;
      return link(commit, row, parent, parentRow, index === 0, height);
    }));
    const lines = svg("svg", { class: "links", width, height: commits.length * height, "aria-hidden": "true" }, links);
    return el("div", { class: "caps", style: `--gutter:${width}px;--row:${height}px` }, lines, commits.map(capsule(zone)));
  }

  /* A station's three zones' items, keyed with `prefix` ("" for yours, "crew-" for Alex's), its
     capsules `height` pixels a row. The files git ignores follow the workshop's own, greyed, and
     its count leaves them out: git does not see them. */
  function stationContents(reading, prefix, height) {
    const files = reading.workshop.map((file) => fileChip(file.path, stateTag(file.state), { "data-state": file.state, "data-key": `${prefix}workshop:${file.path}`, title: t(`zones.tip.${file.state}`) }));
    const ignored = reading.ignored.map((group) => fileChip(group.name, (group.count === 1 ? t("zones.ignoredOne") : t("zones.ignored", { count: group.count })), { class: "file is-ignored art-ignore-field", title: t("zones.tip.ignored") }));
    const workshop = [...files, ...ignored];
    const dock = reading.dock && reading.dock.map((change) => fileChip(change.path, t(`zones.change.${change.change}`), { class: "file is-staged", "data-key": `${prefix}dock:${change.path}` }));
    return {
      [`${prefix}workshop`]: { count: files.length, nodes: workshop },
      [`${prefix}dock`]: reading.dock && { count: dock.length, nodes: dock },
      [`${prefix}vault`]: reading.vault && { count: reading.vault.length, nodes: reading.vault.length ? [capsules(`${prefix}vault`, reading.vault, height)] : [] },
    };
  }

  /* Each zone's items, or null when the zone is off; the crew view's narrower zones take taller
     capsule rows, so a capsule's labels can wrap under its hash. */
  function contents(zones) {
    const height = zones.crew ? CREW_ROW : ROW;
    return {
      ...stationContents(zones, "", height),
      remote: zones.remote && { count: zones.remote.length, nodes: zones.remote.length ? [capsules("remote", zones.remote, height)] : [] },
      ...(zones.crew ? stationContents(zones.crew, "crew-", height) : {}),
    };
  }

  /* A zone's frame; `key` names it on the page ("crew-vault" for Alex's vault), `name` its kind. */
  function zoneShell(key) {
    const name = base(key);
    const title = t(`zones.${name}`);
    const git = t(`zones.${name}Git`);
    const shell = { count: el("span", { class: "z-count" }, "–"), body: el("div", { class: "z-body" }) };
    shell.operation = el("p", { class: "z-op", hidden: true });
    shell.element = el("article", { class: "zone", "data-zone": key, "aria-label": title },
      el("header", { class: "z-head" }, el("span", { class: "zico", "aria-hidden": "true" }), el("div", {}, el("h3", {}, title), el("small", {}, git)), shell.count),
      shell.operation,
      shell.body,
    );
    return shell;
  }

  const flow = (arrows, mirrored = false) => el("div", { class: mirrored ? "flow is-mirror" : "flow", "aria-hidden": "true" },
    arrows.map(([arrow, back]) => el("div", { class: back ? "fl is-back" : "fl", "data-arrow": arrow }, ArtSprites.icon("arrow"), el("span", {}, `git ${base(arrow)}`))));

  /* The four zones in a row, with the arrows between them. */
  const soloRow = (shells) => el("div", { class: "viz-row" }, ZONES.map((name, index) => [shells[name].element, index < FLOWS.length && flow(FLOWS[index])]));

  /* One person's station: their workshop, dock and vault, with the arrows between them. A
     mirrored station (Alex's, on the far side) runs the other way, so its vault faces the
     mothership too. */
  function station(shells, who, prefix, mirrored = false) {
    const row = [shells[`${prefix}workshop`].element, flow([[`${prefix}add`, false]], mirrored), shells[`${prefix}dock`].element, flow([[`${prefix}commit`, false]], mirrored), shells[`${prefix}vault`].element];
    return el("section", { class: `station art-station art-station--${who}${mirrored ? " is-mirror" : ""}`, "data-station": who, "aria-label": t(`zones.station.${who}`) },
      el("p", { class: "art-station-name" }, ArtSprites.icon(`station-${who}`), t(`zones.station.${who}`)),
      el("div", { class: "station-row" }, mirrored ? row.reverse() : row));
  }

  /* Your station, the mothership between the two with each station's push and pull under it
     (Alex's mirrored, as their station is on the other side), and Alex's station as a smaller
     mirror of yours. */
  const crewRows = (shells) => el("div", { class: "viz-crew" },
    station(shells, "you", ""),
    el("div", { class: "crew-sky" }, shells.remote.element, el("div", { class: "crew-flows" }, flow([["push", false], ["pull", true]]), flow([["crew-push", false], ["crew-pull", true]], true))),
    station(shells, "alex", "crew-", true));

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

  /* A copy of the item that moved flies from where it was to where it is now, wearing `looks`
     (classes); the item shows once the copy lands. */
  function fly(from, to, delay, looks) {
    const target = to.getBoundingClientRect();
    if (!from.rect.width) return;
    const ghost = from.node.cloneNode(true);
    ghost.classList.add("ghost", ...looks);
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

  /* In the crew view a capsule rising to the mothership trails a flame, and one landing from it
     a flame above. */
  function trail(element, flight) {
    let classes = [];
    if (element.classList.contains("is-crew") && flight.to.startsWith("remote:")) classes = ["art-crew-flight"];
    else if (element.classList.contains("is-crew") && flight.from.startsWith("remote:")) classes = ["art-crew-flight", "art-crew-flight--down"];
    return classes;
  }

  /* Shows what moved: flights, fades, appearances, bounces, cracks and rises. */
  function move(element, shells, moves, before, timers) {
    moves.flights.forEach((flight, index) => {
      const from = before.get(flight.from);
      const to = find(element, flight.to);
      if (from && to) fly(from, to, index * 120, trail(element, flight));
    });
    for (const key of moves.fades) if (before.has(key)) fade(before.get(key));
    for (const key of moves.appears) if (find(element, key)) appear(find(element, key));
    for (const { from, to } of moves.bounces) if (find(element, from)) bounce(find(element, from), shells[to].element);
    for (const key of moves.cracks) if (find(element, key)) flash(find(element, key), "art-crack", CRACK_MS, timers);
    for (const key of moves.rises) if (find(element, key)) flash(find(element, key), "art-rise-inverted", RISE_MS, timers);
  }

  /* Lights the arrows and wakes the zones, then shows what moved unless motion is reduced. */
  function animate(element, shells, moves, before, { reducedMotion, timers }) {
    for (const command of moves.lit) flash(element.querySelector(`.fl[data-arrow="${command}"]`), "is-lit", LIT_MS, timers);
    for (const name of moves.wake) flash(shells[name].element, "is-waking", LIT_MS, timers);
    if (!reducedMotion) move(element, shells, moves, before, timers);
  }

  /* options: reducedMotion (no flying items; the arrows and zones still light), timers. */
  function create({ reducedMotion = true, timers = window } = {}) {
    const shells = Object.fromEntries([...ZONES, ...CREW].map((key) => [key, zoneShell(key)]));
    const row = soloRow(shells);
    const legend = el("ul", { class: "legend" }, LEGEND.map((state) => el("li", { "data-state": state }, t(`zones.legend.${state}`))));
    const element = el("section", { class: "viz px", "aria-label": t("zones.label") }, row, legend);
    let drawn = null;
    let last = null;
    let crew = false;

    /* Two stations while the level has a teammate, else the row of four. */
    function arrange(withCrew) {
      if (withCrew === crew) return;
      element.firstChild.replaceWith(withCrew ? crewRows(shells) : soloRow(shells));
      element.classList.toggle("is-crew", withCrew);
      crew = withCrew;
    }

    function draw(zones) {
      const filled = contents(zones);
      for (const key of crew ? [...ZONES, ...CREW] : ZONES) {
        const shell = shells[key];
        const zone = filled[key];
        const name = base(key);
        /* A mothership the repository does not name yet: how to name it, and where it lives. */
        const unnamed = key === "remote" && zone && !zones.named;
        shell.element.classList.toggle("is-dormant", !zone || unnamed);
        shell.count.textContent = zone && !unnamed ? String(zone.count) : "–";
        let body = !zone ? [say(OFF[name])] : zone.count ? zone.nodes : [say(EMPTY[name]), ...zone.nodes];
        if (unnamed) body = [say("zones.unnamed.remote"), say("zones.remote.where")];
        shell.body.replaceChildren(...body);
      }
      /* A merge (or rebase, cherry-pick...) stopped halfway is said over the vault. */
      const paused = shells.vault.operation;
      paused.hidden = !zones.operation;
      paused.replaceChildren(...(zones.operation ? [ArtSprites.icon("merging"), t("zones.paused", { operation: zones.operation })] : []));
    }

    return {
      element,

      update(observation) {
        const zones = Zones.read(observation);
        const text = JSON.stringify(zones);
        const before = places(element);
        const moves = last && Zones.moves(last, zones, Typed.gitCommands(observation.commands), Typed.failedGitCommands(observation.commands));
        last = zones;
        arrange(Boolean(zones.crew));
        if (text !== drawn) draw(zones);
        drawn = text;
        if (moves) animate(element, shells, moves, before, { reducedMotion, timers });
      },
    };
  }

  return { create };
})();
