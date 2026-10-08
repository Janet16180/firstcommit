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
 * asks where to start. Needs dom.js, strings.js, art-sprites.js, typed.js, poll.js, playground-summary.js and
 * playground-picture.js (with the pictures it draws). Defines one global, PlaygroundScreen.
 *
 * create(ctx, route) {element, dispose()}: ctx = {game, timers, page, reducedMotion}, route the
 *   playground's address (Route.parse): `picture` names a view to open on.
 */

/* global Dom, Strings, ArtSprites, Typed, Polling, PlaygroundSummary, PlaygroundPicture */
/* exported PlaygroundScreen */

const PlaygroundScreen = (function () {
  const { el } = Dom;
  const { t } = Strings;
  const POLL_MS = 1500;
  const { MAIN, MORE, PER_PERSON } = PlaygroundPicture;
  /* The views that need a mothership: both draw it. */
  const SHARED = ["history", "crew"];
  /* Where History stacks its two sides (orbit.css): a phone. */
  const PHONE = "(max-width: 760px)";

  const tab = (screen, view) => el("button", { type: "button", role: "tab", class: "pg-tab", "data-view": view, onclick: () => pick(screen, view) }, t(`pg.view.${view}`));

  /* Alex is shown when the player chose it and the lab has Alex's clone. */
  const alexShown = (screen) => screen.prefs.alex && Boolean(screen.observation && screen.observation.alex);
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

  function drawTabs(screen) {
    const { ui, prefs } = screen;
    const views = offered(screen);
    for (const button of [...ui.tabs.querySelectorAll(".pg-tab"), ...ui.moreList.querySelectorAll(".pg-tab")]) {
      button.hidden = !views.includes(button.dataset.view);
      button.setAttribute("aria-selected", String(button.dataset.view === prefs.view));
    }
    if (MORE.includes(prefs.view)) ui.more.setAttribute("aria-current", "true");
    else ui.more.removeAttribute("aria-current");
  }

  function drawPicture(screen) {
    const { ui, prefs, ctx } = screen;
    screen.picture = PlaygroundPicture.create(prefs.view, { stacked: window.matchMedia(PHONE).matches, timers: ctx.timers, reducedMotion: ctx.reducedMotion });
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
    const person = whose(screen);
    ui.whose.hidden = !alexShown(screen) || !PER_PERSON.includes(prefs.view);
    for (const button of ui.whose.querySelectorAll("button")) button.setAttribute("aria-pressed", String(button.dataset.whose === person));
    if (!observation) return;
    const reflogRead = screen.reflogRead[person];
    if (prefs.view === "movelog" && reflogRead && screen.live[person] === "unsaid") screen.live[person] = "saying";
    screen.picture.refresh({ observation, whose: person, alexShown: alexShown(screen), reflogRead });
    ui.live.hidden = !(prefs.view === "movelog" && screen.live[person] === "saying");
    if (ui.live.hidden) ui.live.remove();
    else ui.slot.append(ui.live);
    ui.foldLine.textContent = PlaygroundSummary.line({ view: prefs.view, whose: alexShown(screen) ? person : null, project: observation[person].project });
  }

  /* Takes a look at the lab: what it shows, whether git reflog was typed, and whether a conflict
     is still there to show. */
  function take(screen, observation) {
    screen.observation = observation;
    for (const person of ["you", "alex"]) {
      const side = observation[person];
      if (side && Typed.gitCommands(side.commands).includes("reflog")) screen.reflogRead[person] = true;
    }
    const side = observation[whose(screen)];
    screen.conflictKept = side.markers.length > 0 || (screen.conflictKept && side.project.operation === "merge");
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

  /* The night bar the level screen has, with the way back to the map; the start's name when one is open. */
  const head = (start) => el("header", { class: "hud pg-head" },
    el("a", { class: "btn", href: "#/", "aria-label": t("level.mapTip") }, ArtSprites.icon("back"), el("span", { class: "lbl" }, t("level.map"))),
    el("div", { class: "hud-title" }, el("h1", { class: "hud-name pg-title" }, t("pg.title")), start && el("span", { class: "hud-num pg-start" }, start.title)));

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

  function whoseSwitch(screen) {
    const button = (person) => el("button", { type: "button", class: "pg-whose-button", "data-whose": person, "aria-pressed": "false", onclick: () => pickWhose(screen, person) }, t(`pg.whose.${person}`));
    return el("div", { class: "pg-whose", role: "group", "aria-label": t("pg.picture"), hidden: true },
      el("span", { class: "pg-whose-label" }, t("pg.picture")), button("you"), button("alex"));
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

  /* The playground for the current start: its preferences, a view named by the address first. */
  function build(screen, playground) {
    const { route, ui } = screen;
    screen.start = playground.starts.find((start) => start.id === playground.current.start);
    screen.prefs = { ...playground.prefs };
    if (route.picture && [...MAIN, ...MORE].includes(route.picture)) screen.prefs.view = route.picture;
    ui.down = el("p", { class: "pg-down", role: "alert", hidden: true }, t("pg.down"));
    ui.whose = whoseSwitch(screen);
    ui.terms = el("div", { class: "pg-terms" });
    screen.element.replaceChildren(head(screen.start), ui.down,
      el("div", { class: "pg-body" },
        el("div", { class: "pg-left" }, viewRow(screen), ui.whose, pictured(screen)),
        ui.terms));
    drawPicture(screen);
    screen.poll = Polling.start({ tick: () => tick(screen), intervalMs: POLL_MS, timers: screen.ctx.timers, page: screen.ctx.page });
  }

  async function choose(screen, id) {
    screen.element.replaceChildren(el("p", { class: "pg-starting", role: "status" }, t("pg.starting")));
    const playground = await screen.ctx.game.playgroundStart(id);
    if (!screen.disposed) build(screen, playground);
  }

  function picker(screen, playground) {
    screen.element.replaceChildren(
      head(null),
      el("h2", { class: "pg-choose" }, t("pg.choose")),
      el("ul", { class: "pg-choices" }, playground.starts.map((start) => el("li", {},
        el("button", { type: "button", class: "pg-choice", "data-start": start.id, onclick: () => choose(screen, start.id) },
          el("b", { class: "pg-choice-title" }, start.title),
          el("span", { class: "pg-choice-blurb" }, start.blurb))))));
  }

  async function open(screen) {
    const playground = await screen.ctx.game.playground();
    if (screen.disposed) return;
    if (playground.current) build(screen, playground);
    else picker(screen, playground);
  }

  function create(ctx, route) {
    const screen = {
      ctx,
      route,
      element: el("section", { class: "pg", "aria-label": t("pg.title") }),
      ui: {},
      start: null,
      prefs: null,
      observation: null,
      picture: null,
      poll: null,
      disposed: false,
      conflictKept: false,
      reflogRead: { you: false, alex: false },
      live: { you: "unsaid", alex: "unsaid" },
    };
    open(screen);
    return {
      element: screen.element,
      dispose() {
        screen.disposed = true;
        if (screen.poll) screen.poll.stop();
      },
    };
  }

  return { create };
})();
