"use strict";

/*
 * The page's composition root: it builds the API client, the views and the terminal, routes
 * the address to a view, keeps the header and the view preferences (light or dark, sound), and
 * shows what goes wrong. It holds no game rule and no game state beyond the last dashboard the
 * server sent (refreshed on every view change). Loads last; defines no global.
 */

/* global createClient, createTerminal, createGameApi, Dom, Route, Sound, Celebrate, Dialog, TimeTheme, TimeMotion, TimeGuide, Progress, HomeView, LevelPage, CardsView, NotesView */

(function () {
  const { el } = Dom;
  const THEME_KEY = "firstcommit.theme";
  const THEMES = ["auto", "light", "dark"];
  const TOAST_MS = 9000;
  const MONO = "\"Cascadia Mono\", \"DejaVu Sans Mono\", \"Liberation Mono\", Menlo, Consolas, monospace";
  const TERMINAL_LOOKS = {
    light: { fontFamily: MONO, theme: TimeTheme.terminal.light },
    dark: { fontFamily: MONO, theme: TimeTheme.terminal.dark },
  };
  const VIEWS = {
    home: (ctx) => HomeView.create(ctx),
    level: (ctx, route) => LevelPage.create(ctx, route.id),
    cards: (ctx, route) => CardsView.create(ctx, route.chapter),
    notes: (ctx, route) => NotesView.create(ctx, route.chapter),
  };
  const TITLES = { home: "Map", level: "Level", cards: "Cards", notes: "Notes" };

  /* client.js removes the fragment when it carries the access key; keep the address part first. */
  const firstAddress = location.hash.split("&")[0];
  const app = { status: null, view: null, turn: 0, terminal: null, terminalFor: null, locked: false };
  const client = createClient({ header: "X-FirstCommit-Token", storageKey: "firstcommit.token", command: "firstcommit", onLocked: () => showLocked() });
  const game = createGameApi(client.api);
  const mapGuide = TimeGuide.create({ figures: game.guide });
  const main = document.getElementById("app");
  const darkScheme = window.matchMedia("(prefers-color-scheme: dark)");

  function readTheme() {
    try {
      return THEMES.includes(localStorage.getItem(THEME_KEY)) ? localStorage.getItem(THEME_KEY) : "auto";
    } catch (error) {
      return "auto"; /* Storage is blocked: follow the system for this visit. */
    }
  }

  let themeChoice = readTheme();
  const shownTheme = () => (themeChoice === "auto" ? (darkScheme.matches ? "dark" : "light") : themeChoice);

  function applyTheme() {
    document.documentElement.dataset.theme = shownTheme();
    const button = document.querySelector(".pref-theme");
    button.textContent = { auto: "Look: system", light: "Look: light", dark: "Look: dark" }[themeChoice];
    if (app.terminal) app.terminal.setLook(shownTheme(), "Terminal");
  }

  function cycleTheme() {
    themeChoice = THEMES[(THEMES.indexOf(themeChoice) + 1) % THEMES.length];
    try {
      localStorage.setItem(THEME_KEY, themeChoice);
    } catch (error) {
      /* Storage is blocked: the choice lasts for this visit. */
    }
    applyTheme();
  }

  function renderSound() {
    const button = document.querySelector(".pref-sound");
    button.textContent = Sound.isEnabled() ? "Sound: on" : "Sound: off";
    button.setAttribute("aria-pressed", String(Sound.isEnabled()));
  }

  function renderHeader() {
    const { status } = app;
    const player = document.querySelector(".player");
    player.hidden = !status;
    if (!status) return;
    player.querySelector(".player-rank").textContent = status.rank.title;
    player.querySelector(".player-xp").textContent = `${status.xp} XP`;
    player.querySelector(".meter i").style.width = `${Math.round(Progress.rankProgress(status).fraction * 100)}%`;
    const badge = document.querySelector(".nav .badge");
    badge.hidden = status.cards_due === 0;
    badge.textContent = String(status.cards_due);
    badge.setAttribute("aria-label", `${status.cards_due} due`);
  }

  function toast(message) {
    const item = el("div", { class: "toast", role: "alert" },
      el("p", {}, message),
      el("button", { type: "button", class: "link-button", onclick: () => item.remove() }, "Dismiss"),
    );
    document.querySelector(".toasts").append(item);
    setTimeout(() => item.remove(), TOAST_MS);
  }

  /* A 500 says its kind in the reply: "save" for a damaged save file. Anything else, a 500
     without a kind included, is a bug, which starting over would not fix. */
  const damagedSave = (error) => error.status === 500 && Boolean(error.data) && error.data.kind === "save";
  const BUG_DETAILS = "The details are in the terminal where firstcommit is running.";

  /* The last resort for errors no view handled. */
  function report(error) {
    if (app.locked || (error && error.status === 403)) return;
    const status = error ? error.status : undefined;
    const detail = error && error.message ? error.message : String(error);
    let message = `Something went wrong: ${detail}`;
    if (status === 0) message = "The game server did not answer. Is `firstcommit` still running in your terminal?";
    else if (damagedSave(error)) message = `Your saved game is damaged: ${detail}. Open the map to start over.`;
    else if (status === 500) message = `The game hit a bug: ${detail}. ${BUG_DETAILS}`;
    toast(message);
  }

  function showScreen(title, ...body) {
    if (app.view && app.view.dispose) app.view.dispose();
    app.view = null;
    main.replaceChildren(el("section", { class: "panel narrow fatal" }, el("h1", {}, title), ...body));
  }

  function showLocked() {
    showScreen("Open the game from its link", el("p", {}, "This page needs the link that ", el("code", {}, "firstcommit"), " printed in your terminal when it started: the link carries the key that lets the page talk to the game."), el("p", {}, "Find the line that starts with http://localhost in that terminal and open it (Ctrl+click in most terminals)."));
    app.locked = true;
  }

  async function startOver() {
    const sure = await Dialog.confirm({
      title: "Start over?",
      text: "This erases your progress and makes a fresh save. It cannot be undone.",
      confirm: "Start over",
      cancel: "Not now",
      danger: true,
    });
    if (!sure) return;
    await game.reset();
    show(Route.parse(location.hash));
  }

  function showBug(message) {
    showScreen("The game hit a bug",
      el("p", {}, message),
      el("p", {}, BUG_DETAILS, " Starting over would not help: try again, and if it keeps happening, those details say what went wrong."),
      el("div", { class: "actions" }, el("button", { type: "button", class: "btn btn-primary", onclick: () => show(Route.parse(location.hash)) }, "Try again")),
    );
  }

  function showDamaged(message) {
    showScreen("Your saved game is damaged",
      el("p", {}, message),
      el("p", {}, "This happens when a save file is edited by hand or cut short. Starting over makes a fresh save; you can also run ", el("code", {}, "firstcommit reset --yes"), " in a terminal."),
      el("div", { class: "actions" }, el("button", { type: "button", class: "btn btn-danger start-over", onclick: startOver }, "Start over")),
    );
  }

  function disposeTerminal() {
    if (app.terminal) app.terminal.dispose();
    app.terminal = null;
    app.terminalFor = null;
  }

  /* One shell per level started: it lives while that level is in progress, even while the
     player looks at other views, and is replaced when another level starts. */
  const terminal = {
    attach(host) {
      const key = app.status.active ? app.status.active.started : null;
      if (app.terminal && app.terminalFor !== key) disposeTerminal();
      if (!app.terminal) {
        app.terminal = createTerminal({ protocol: "firstcommit", token: client.token, command: "firstcommit", looks: TERMINAL_LOOKS, storagePrefix: "firstcommit.", openFromHeight: 0, onUnreachable: probe });
        app.terminalFor = key;
        app.terminal.setLook(shownTheme(), "Terminal");
      }
      host.append(app.terminal.element);
      app.terminal.start();
    },
    detach() {
      const still = app.status && app.status.active && app.status.active.started === app.terminalFor;
      if (!still) disposeTerminal();
      else if (app.terminal) app.terminal.element.remove();
    },
    type: (text) => app.terminal && app.terminal.type(text),
  };

  /* A refused WebSocket looks like a network failure; asking the API tells a stale key apart
     (client.js then shows the locked screen). Its own failure is already shown in the terminal. */
  function probe() {
    game.status().catch(() => null);
  }

  async function refresh() {
    app.status = await game.status();
    renderHeader();
    return app.status;
  }

  async function celebrate(options) {
    Sound.play("celebrate");
    if (options.rankBefore !== options.rankAfter) setTimeout(() => Sound.play("rankup"), 1500);
    await Celebrate.show(options);
  }

  const ctx = {
    game,
    status: () => app.status,
    refresh,
    reload: () => show(Route.parse(location.hash)),
    celebrate,
    sound: Sound,
    timers: window,
    page: document,
    theme: TimeTheme.withGuide(mapGuide),
    panelWords: TimeTheme.panel,
    playMap: TimeMotion.playMap,
    reducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    terminal,
  };

  /* Shows the view for an address; a newer navigation that starts while this one waits wins. */
  async function show(route) {
    if (app.locked) return;
    if (app.view && app.view.dispose) app.view.dispose();
    app.view = null;
    app.turn += 1;
    const turn = app.turn;
    try {
      await refresh();
    } catch (error) {
      if (error.status === 0) showScreen("Cannot reach the game", el("p", {}, "Is ", el("code", {}, "firstcommit"), " still running in your terminal? Start it again and open the link it prints."));
      else if (damagedSave(error)) showDamaged(error.message);
      else if (error.status === 500) showBug(error.message);
      else if (error.status !== 403) throw error;
      return;
    }
    if (turn !== app.turn) return;
    app.view = VIEWS[route.view](ctx, route);
    main.replaceChildren(app.view.element);
    document.title = `${TITLES[route.view]} · First Commit`;
    for (const link of document.querySelectorAll(".nav a")) link.toggleAttribute("aria-current", link.dataset.view === route.view);
    main.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }

  /* Tab completes in the shell; Shift+Tab leaves the terminal, so the keyboard is never trapped. */
  function releaseTerminalFocus(event) {
    if (event.key === "Tab" && event.shiftKey && event.target.closest && event.target.closest(".term-host")) event.stopPropagation();
  }

  function boot() {
    applyTheme();
    renderSound();
    darkScheme.addEventListener("change", applyTheme);
    document.querySelector(".pref-theme").addEventListener("click", cycleTheme);
    document.querySelector(".pref-sound").addEventListener("click", () => {
      Sound.setEnabled(!Sound.isEnabled());
      renderSound();
    });
    for (const type of ["pointerdown", "keydown"]) document.addEventListener(type, Sound.unlock);
    document.addEventListener("keydown", releaseTerminalFocus, true);
    document.addEventListener("keydown", (event) => app.view && app.view.keydown && app.view.keydown(event));
    window.addEventListener("unhandledrejection", (event) => report(event.reason));
    window.addEventListener("error", (event) => report(event.error || event.message));
    window.addEventListener("hashchange", () => show(Route.parse(location.hash)));
    if (!client.token()) {
      showLocked();
      return;
    }
    if (firstAddress.startsWith("#/") && location.hash !== firstAddress) history.replaceState(null, "", firstAddress);
    show(Route.parse(location.hash));
  }

  boot();
})();
