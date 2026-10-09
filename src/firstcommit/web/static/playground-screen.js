"use strict";

/*
 * The playground (docs/drafts/playground/plan.md): free play in a practice repository, with no
 * goals, stars or coaching. A head with its name and the starting point's; the views (Chain,
 * History, Desk and Crew, Conflict while a file has markers, and Move log and Graph under More
 * views); while Alex is shown, the choice of whose repository a per-person view draws; and one
 * picture (playground-picture.js), drawn live from the lab every POLL_MS. The picture's legend
 * folds behind "i", and on a phone the picture starts folded into one line saying what it shows
 * (playground-summary.js). The move log stays empty until `git reflog` is typed in that
 * repository, then says once that it is live. The view, Alex shown and whose repository are
 * the current start's preferences, saved on the server at each change. With no start yet, it
 * asks where to start. Needs dom.js, strings.js, art-sprites.js, progress.js, dialog.js, typed.js, poll.js, editor-strip.js, playground-summary.js and
 * playground-picture.js (with the pictures it draws). Defines one global, PlaygroundScreen.
 *
 * Your terminal is on the right, and Alex's under it while Alex is shown (Show or Hide Alex's
 * terminal, absent where there is no mothership); on a phone one shows at a time, chosen by the
 * same switch that chooses whose repository the picture draws. While an editor runs in a
 * terminal (its title says so), the editor strip stands above it; while the game's merge tool
 * waits in one (`git mergetool`), its panel (merge-tool.js) stands above it, for that person's
 * repository.
 *
 * create(ctx, route) {element, dispose()}: ctx = {game, timers, page, reducedMotion,
 *   playTerminals: {attach(person, host, started, onTitle(title, at), onClose()), detach(),
 *   type(person, text), keys(person, keys)}}, the shells kept by the page for
 *   the start built at `started`; route the playground's address (Route.parse): `picture` names a
 *   view to open on.
 */

/* global Dom, Strings, ArtSprites, Progress, Dialog, Typed, Polling, EditorStrip, MergeTool, PlaygroundSummary, PlaygroundPicture */
/* exported PlaygroundScreen */

const PlaygroundScreen = (function () {
  const { el } = Dom;
  const { t } = Strings;
  const POLL_MS = 1500;
  /* Ctrl-C, as the terminal sends it: the game's merge tool reads it as Cancel. */
  const CTRL_C = "\x03";
  const { MAIN, MORE, PER_PERSON } = PlaygroundPicture;
  /* The views that need a mothership: both draw it. */
  const SHARED = ["history", "crew"];
  /* Where History stacks its two sides (orbit.css): a phone. */
  const PHONE = "(max-width: 760px)";

  const tab = (screen, view) => el("button", { type: "button", role: "tab", class: "pg-tab", "data-view": view, onclick: () => pick(screen, view) }, t(`pg.view.${view}`));

  /* Alex is shown when the player chose it and the lab has Alex's clone (a start with a mothership
     has one; the lab says so once looked at). */
  const alexShown = (screen) => screen.prefs.alex && screen.start.mothership && (!screen.observation || Boolean(screen.observation.alex));
  const whose = (screen) => (alexShown(screen) ? screen.prefs.whose : "you");

  /* The views to offer now: History and Crew need a mothership, Conflict a file with markers or
     the merge they belong to (before the first look, the view the start opens on). */
  function offered(screen) {
    const { start, observation } = screen;
    const conflict = observation ? screen.conflictKept : screen.prefs.view === "conflict";
    return [...MAIN, ...MORE].filter((view) => (!SHARED.includes(view) || start.mothership) && (view !== "conflict" || conflict));
  }

  function savePrefs(screen) {
    const { view, alex, whose: chosen } = screen.prefs;
    return screen.ctx.game.playgroundPrefs({ view, alex, whose: chosen });
  }

  function pick(screen, view) {
    for (const person of ["you", "alex"]) if (screen.live[person] === "saying") screen.live[person] = "said";
    screen.prefs.view = view;
    screen.ui.moreList.hidden = true;
    screen.ui.more.setAttribute("aria-expanded", "false");
    drawPicture(screen);
    savePrefs(screen);
  }

  function pickWhose(screen, person) {
    screen.prefs.whose = person;
    refresh(screen);
    savePrefs(screen);
  }

  function toggleAlex(screen) {
    screen.prefs.alex = !screen.prefs.alex;
    refresh(screen);
    savePrefs(screen);
  }

  /* The terminals: yours, and Alex's under it while Alex is shown (its shell opened the first time);
     on a phone the switch shows one of them, the one whose repository the picture draws. */
  function drawTerms(screen) {
    const { ui, ctx } = screen;
    const shown = alexShown(screen);
    const person = whose(screen);
    ui.frames.alex.element.hidden = !shown;
    ui.terms.classList.toggle("is-two", shown);
    if (shown && !screen.alexAttached) {
      screen.alexAttached = true;
      ctx.playTerminals.attach("alex", ui.frames.alex.host, screen.started, titled(screen, "alex"), () => ui.frames.alex.tool.closed());
    }
    if (ui.alexToggle) {
      ui.alexToggle.setAttribute("aria-checked", String(shown));
      ui.alexLabel.textContent = t(shown ? "pg.alex.hide" : "pg.alex.show");
    }
    ui.termSwitch.hidden = !shown;
    for (const button of ui.termSwitch.querySelectorAll("button")) button.setAttribute("aria-pressed", String(button.dataset.whose === person));
    ui.terms.dataset.whose = person;
  }

  function drawTabs(screen) {
    const { ui, prefs } = screen;
    const views = offered(screen);
    for (const button of [...ui.tabs.querySelectorAll(".pg-tab"), ...ui.moreList.querySelectorAll(".pg-tab")]) {
      button.hidden = !views.includes(button.dataset.view);
      button.setAttribute("aria-selected", String(button.dataset.view === prefs.view));
    }
    const more = MORE.includes(prefs.view);
    if (more) ui.more.setAttribute("aria-current", "true");
    else ui.more.removeAttribute("aria-current");
    ui.more.textContent = more ? t("pg.moreOn", { view: t(`pg.view.${prefs.view}`) }) : t("pg.more");
  }

  function drawPicture(screen) {
    const { ui, prefs, ctx } = screen;
    screen.picture = PlaygroundPicture.create(prefs.view, {
      stacked: window.matchMedia(PHONE).matches,
      timers: ctx.timers,
      reducedMotion: ctx.reducedMotion,
      onWrite: async (request) => {
        await ctx.game.playgroundResolve(request);
        await tick(screen);
      },
      onType: (person, line) => ctx.playTerminals.type(person, line),
    });
    ui.slot.replaceChildren(screen.picture.element);
    refresh(screen);
    const chosen = [...ui.tabs.querySelectorAll(".pg-tab")].find((button) => button.dataset.view === prefs.view);
    if (chosen) chosen.scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  /* Redraws what depends on the lab: the tabs, whose switch, the picture, its folded line and
     the move log's note. */
  function refresh(screen) {
    const { ui, prefs, observation } = screen;
    drawTabs(screen);
    drawTerms(screen);
    const person = whose(screen);
    ui.whose.hidden = !alexShown(screen) || !PER_PERSON.includes(prefs.view);
    for (const button of ui.whose.querySelectorAll("button")) button.setAttribute("aria-pressed", String(button.dataset.whose === person));
    if (!observation) return;
    const reflogRead = screen.reflogRead[person];
    if (prefs.view === "movelog" && reflogRead && screen.live[person] === "unsaid") screen.live[person] = "saying";
    screen.picture.refresh({ observation, whose: person, alexShown: alexShown(screen), reflogRead, editing: screen.editing });
    ui.live.hidden = !(prefs.view === "movelog" && screen.live[person] === "saying");
    if (ui.live.hidden) ui.live.remove();
    else ui.slot.append(ui.live);
    ui.foldLine.textContent = PlaygroundSummary.line({ view: prefs.view, whose: alexShown(screen) ? person : null, project: observation[person].project });
  }

  /* The lab by person: each one's repository with their desk, the lines typed since the page last
     looked (the zones' arrows), and git's drawing, empty without a repository. */
  function bySide(screen, observation) {
    const side = (person, project) => {
      const desk = observation[person];
      if (!desk) return null;
      const commands = desk.typed.slice(screen.typedSeen[person]);
      screen.typedSeen[person] = desk.typed.length;
      return { ...desk, project, commands, graph: desk.graph || [] };
    };
    return { github: observation.github, you: side("you", observation.project), alex: side("alex", observation.teammate) };
  }

  /* Takes a look at the lab: what it shows, whether git reflog was typed, whether the line to try
     has run, and whether a conflict is still there to show. */
  function take(screen, observation) {
    screen.observation = bySide(screen, observation);
    for (const person of ["you", "alex"]) {
      const side = observation[person];
      if (side) screen.ui.frames[person].tool.update({ person, marked: side.marked, texts: side.texts });
      if (side && Typed.gitCommands(side.typed).includes("reflog")) screen.reflogRead[person] = true;
    }
    const ran = observation.you.typed.some((command) => command.line.trim() === (screen.tryLine || "").trim());
    if (ran) screen.ui.frames.you.chip.hidden = true;
    const side = screen.observation[whose(screen)];
    screen.conflictKept = side.marked.length > 0 || (screen.conflictKept && side.project.operation === "merge");
    if (offered(screen).includes(screen.prefs.view)) refresh(screen);
    else pick(screen, "chain");
  }

  async function tick(screen) {
    let observation = null;
    try {
      observation = await screen.ctx.game.playgroundObserve();
    } catch (error) {
      if (error.status !== 0) throw error;
    }
    if (screen.disposed) return;
    screen.ui.down.hidden = observation !== null;
    if (observation) take(screen, observation);
  }

  /* The night bar the level screen has, with the way back to the map, the start's name, Start over
     and Other start, and the way back to the mission the playground was opened from. */
  function head(screen) {
    const { start, ctx } = screen;
    const back = ctx.back();
    const number = back ? Progress.missionNumber(ctx.status().chapters, back) : null;
    return el("header", { class: "hud pg-head" },
      el("a", { class: "btn", href: "#/", "aria-label": t("level.mapTip") }, ArtSprites.icon("back"), el("span", { class: "lbl" }, t("level.map"))),
      el("div", { class: "hud-title" }, el("h1", { class: "hud-name pg-title" }, t("pg.title")), start && el("span", { class: "hud-num pg-start" }, start.title)),
      start && el("button", { type: "button", class: "btn pg-over", onclick: () => startOver(screen) }, t("pg.over")),
      start && el("button", { type: "button", class: "btn pg-other", onclick: () => picker(screen) }, t("pg.other")),
      number && el("a", { class: "btn pg-back", href: `#/level/${encodeURIComponent(back)}` }, t("pg.back", { number: number.number })));
  }

  function viewRow(screen) {
    const { ui } = screen;
    ui.tabs = el("div", { class: "pg-tabs", role: "tablist", "aria-label": t("pg.views") }, MAIN.map((view) => tab(screen, view)));
    ui.moreList = el("div", { class: "pg-more-list", role: "tablist", hidden: true }, MORE.map((view) => tab(screen, view)));
    ui.more = el("button", { type: "button", class: "pg-more-button", "aria-expanded": "false", onclick: () => {
      ui.moreList.hidden = !ui.moreList.hidden;
      ui.more.setAttribute("aria-expanded", String(!ui.moreList.hidden));
    } }, t("pg.more"));
    return el("nav", { class: "pg-views" }, ui.tabs, el("div", { class: "pg-more" }, ui.more, ui.moreList));
  }

  /* A labelled pair of buttons choosing whose repository: "Picture:" over the picture, "Terminal:"
     over the terminals on a phone. */
  function personSwitch(screen, { kind, label, words }) {
    const button = (person) => el("button", { type: "button", class: "pg-whose-button", "data-whose": person, "aria-pressed": "false", onclick: () => pickWhose(screen, person) }, t(`${words}.${person}`));
    return el("div", { class: kind, role: "group", "aria-label": t(label), hidden: true },
      el("span", { class: "pg-whose-label" }, t(label)), button("you"), button("alex"));
  }

  /* A terminal's frame: its name, the editor strip while an editor runs in it, the merge tool's
     panel while the game's merge tool waits in it, and its shell. */
  function frame(screen, person) {
    const host = el("div", { class: "pg-term-host" });
    const strip = EditorStrip.create({ onKeys: (keys) => screen.ctx.playTerminals.keys(person, keys), timers: screen.ctx.timers });
    const tool = MergeTool.create({
      timers: screen.ctx.timers,
      onWrite: async ({ file, read, choices }) => {
        await screen.ctx.game.playgroundResolve({ person, file, read, choices });
        await tick(screen);
      },
      onCancel: () => screen.ctx.playTerminals.keys(person, CTRL_C),
    });
    const line = person === "you" ? screen.tryLine : null;
    const chip = line ? el("button", { type: "button", class: "pg-try", onclick: () => screen.ctx.playTerminals.type("you", line) }, t("pg.try", { line })) : null;
    const element = el("section", { class: "pg-term termcol", "data-who": person, "aria-label": t(`pg.term.${person}`) }, el("h2", { class: "pg-term-name" }, t(`pg.term.${person}`)), strip.element, tool.element, chip, host);
    return { host, strip, tool, chip, element };
  }

  /* What the terminal's title says runs in it: the strip shows the editor's keys, and the
     conflict panel waits while the editor has a file. */
  const titled = (screen, person) => (title, at) => {
    screen.ui.frames[person].tool.title(title, at);
    screen.editing[person] = EditorStrip.parse(title);
    screen.ui.frames[person].strip.show(screen.editing[person]);
    if (screen.picture) refresh(screen);
  };

  function termColumn(screen) {
    const { ui, start } = screen;
    ui.frames = { you: frame(screen, "you"), alex: frame(screen, "alex") };
    ui.termSwitch = personSwitch(screen, { kind: "pg-termswitch", label: "pg.terminal", words: "pg.who" });
    ui.alexLabel = el("span", { class: "pg-alex-label" });
    ui.alexToggle = start.mothership ? el("button", { type: "button", role: "switch", "aria-checked": "false", class: "pg-alex-toggle", onclick: () => toggleAlex(screen) }, el("span", { class: "pg-switch", "aria-hidden": "true" }), ui.alexLabel) : null;
    ui.terms = el("div", { class: "pg-terms" }, ui.alexToggle, ui.termSwitch, ui.frames.you.element, ui.frames.alex.element);
    return ui.terms;
  }

  function pictured(screen) {
    const { ui } = screen;
    ui.foldLine = el("span", { class: "pg-fold-line" });
    ui.fold = el("button", { type: "button", class: "pg-fold", "aria-expanded": "false", title: t("pg.unfold"), onclick: () => {
      const folded = ui.pictured.classList.toggle("is-folded");
      ui.fold.setAttribute("aria-expanded", String(!folded));
      ui.fold.title = t(folded ? "pg.unfold" : "pg.fold");
    } }, ui.foldLine);
    ui.key = el("button", { type: "button", class: "pg-key", "aria-pressed": "false", "aria-label": t("pg.key"), title: t("pg.key"), onclick: () => {
      ui.key.setAttribute("aria-pressed", String(ui.pictured.classList.toggle("is-keyed")));
    } }, "i");
    ui.slot = el("div", { class: "pg-slot" });
    ui.live = el("p", { class: "pg-live", hidden: true }, Strings.parts("pg.live").map((part) => (typeof part === "string" ? part : el("code", {}, part.code))));
    ui.pictured = el("div", { class: "pg-pictured is-folded" }, ui.fold, ui.key, ui.slot);
    return ui.pictured;
  }

  /* Everything that belongs to one build of a start, as it is before the first look. */
  function fresh(screen) {
    if (screen.poll) screen.poll.stop();
    Object.assign(screen, {
      observation: null,
      picture: null,
      poll: null,
      alexAttached: false,
      conflictKept: false,
      reflogRead: { you: false, alex: false },
      typedSeen: { you: 0, alex: 0 },
      editing: { you: null, alex: null },
      live: { you: "unsaid", alex: "unsaid" },
    });
  }

  /* The playground for the current start, on the view its preferences name, or the address's the
     first time; the address's line to try shows only in the start it was meant for. */
  function build(screen, playground) {
    const { route, ui } = screen;
    fresh(screen);
    screen.playground = playground;
    const { start: id, started, view, alex, whose: chosen } = playground.current;
    screen.start = playground.starts.find((start) => start.id === id);
    screen.started = started;
    screen.prefs = { view, alex, whose: chosen };
    const meant = !route.start || route.start === screen.start.id;
    if (meant && [...MAIN, ...MORE].includes(route.picture)) screen.prefs.view = route.picture;
    screen.tryLine = meant ? route.tryLine : null;
    screen.route = { ...route, picture: null, tryLine: null };
    ui.down = el("p", { class: "pg-down", role: "alert", hidden: true }, t("pg.down"));
    ui.whose = personSwitch(screen, { kind: "pg-whose", label: "pg.picture", words: "pg.whose" });
    ui.body = el("div", { class: "pg-body" },
      el("div", { class: "pg-left" }, viewRow(screen), ui.whose, pictured(screen)),
      termColumn(screen));
    screen.element.replaceChildren(head(screen), ui.down, ui.body);
    screen.ctx.playTerminals.attach("you", ui.frames.you.host, screen.started, titled(screen, "you"), () => ui.frames.you.tool.closed());
    drawPicture(screen);
    screen.poll = Polling.start({ tick: () => tick(screen), intervalMs: POLL_MS, timers: screen.ctx.timers, page: screen.ctx.page });
  }

  async function begin(screen, id) {
    fresh(screen);
    screen.element.replaceChildren(el("p", { class: "pg-starting", role: "status" }, t("pg.starting")));
    const playground = await screen.ctx.game.playgroundStart(id);
    if (!screen.disposed) build(screen, playground);
  }

  /* Asks before a lab is built again over the current one: what goes, and what never does. */
  function sure(screen, start) {
    const again = start.id === screen.start.id;
    const kind = again ? "pg.overAsk" : "pg.otherAsk";
    return Dialog.confirm({ title: t(`${kind}.title`, { title: start.title }), text: t(`${kind}.text`, { title: start.title }), confirm: t(`${kind}.confirm`), cancel: t("pg.keepPlaying"), danger: true });
  }

  async function startOver(screen) {
    if (await sure(screen, screen.start)) await begin(screen, screen.start.id);
  }

  /* A start chosen in the picker: built at once the first time, else after asking. */
  async function choose(screen, start) {
    if (screen.start && !(await sure(screen, start))) return;
    await begin(screen, start.id);
  }

  function closePicker(screen) {
    screen.ui.picker.remove();
    screen.ui.body.hidden = false;
  }

  /* The starting points, each with the chapters whose commands it uses (none is locked); over the
     playground, with Cancel, when a start is already open. */
  function picker(screen) {
    const { ui, playground } = screen;
    const choice = (start) => el("li", {},
      el("button", { type: "button", class: "pg-choice", "data-start": start.id, onclick: () => choose(screen, start) },
        el("b", { class: "pg-choice-title" }, start.title),
        el("span", { class: "pg-choice-blurb" }, start.blurb),
        start.uses.length > 0 && el("span", { class: "pg-choice-uses" }, t("pg.uses", { chapters: start.uses.map((chapter) => chapter.title).join(", ") }))));
    ui.picker = el("section", { class: "pg-picker" },
      el("h2", { class: "pg-choose" }, t("pg.choose")),
      el("ul", { class: "pg-choices" }, playground.starts.map(choice)),
      el("p", { class: "pg-choose-note" }, t("pg.chooseNote")),
      screen.start && el("button", { type: "button", class: "btn pg-choose-cancel", onclick: () => closePicker(screen) }, t("pg.cancel")));
    if (!screen.start) {
      screen.element.replaceChildren(head(screen), ui.picker);
      return;
    }
    ui.body.hidden = true;
    screen.element.append(ui.picker);
  }

  /* Opens the current start, or the one the address names (asking first when that replaces
     another), or asks where to start. */
  async function open(screen) {
    const playground = await screen.ctx.game.playground();
    if (screen.disposed) return;
    screen.playground = playground;
    const { current } = playground;
    const wanted = playground.starts.find((start) => start.id === screen.route.start);
    if (!wanted || (current && current.start === wanted.id)) {
      if (current) build(screen, playground);
      else picker(screen);
      return;
    }
    if (!current) {
      await begin(screen, wanted.id);
      return;
    }
    const asked = screen.route;
    build(screen, playground);
    if (!(await sure(screen, wanted))) return;
    screen.route = asked;
    await begin(screen, wanted.id);
  }

  function create(ctx, route) {
    const screen = {
      ctx,
      route,
      element: el("section", { class: "pg", "aria-label": t("pg.title") }),
      ui: {},
      playground: null,
      start: null,
      prefs: null,
      started: null,
      tryLine: null,
      disposed: false,
    };
    fresh(screen);
    open(screen);
    return {
      element: screen.element,
      dispose() {
        screen.disposed = true;
        if (screen.poll) screen.poll.stop();
        if (screen.started) ctx.playTerminals.detach();
      },
    };
  }

  return { create };
})();
