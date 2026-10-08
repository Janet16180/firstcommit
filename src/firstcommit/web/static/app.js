"use strict";

/*
 * The page's composition root: it builds the API client, the views and the terminal, routes
 * the address to a view, keeps the header and the view preferences (light or dark, sound,
 * English or Spanish), and
 * shows what goes wrong. It holds no game rule and no game state beyond the last dashboard the
 * server sent (refreshed on every view change). The map and the level screen have their own
 * heads, so the header bar shows only over the cards and the notes; the preference buttons
 * also sit in the map's bar. Loads last; defines no global.
 */

/* global createClient, createTerminal, createGameApi, Dom, Strings, Route, Sound, Dialog, ArtSky, Progress, StarMap, LevelScreen, FieldGuide, CardsView, NotesView, DevList, PlaygroundScreen */

(function () {
  const { el } = Dom;
  const { t } = Strings;
  const THEME_KEY = "firstcommit.theme";
  const THEMES = ["auto", "light", "dark"];
  const TOAST_MS = 9000;
  const MONO = "\"Cascadia Mono\", \"DejaVu Sans Mono\", \"Liberation Mono\", Menlo, Consolas, monospace";
  /* The design's terminal: VT323 at the design's size, always night, in both looks. */
  const TERMINAL_FONT = `VT323, ${MONO}`;
  const TERMINAL_SIZE = 19;
  const CRT = {
    background: "#120F2C",
    foreground: "#FFE6B0",
    cursor: "#FFD25A",
    cursorAccent: "#120F2C",
    selectionBackground: "#3A3470",
    black: "#1B1740",
    red: "#FF8A78",
    green: "#9EF0A0",
    yellow: "#FFD25A",
    blue: "#8ADBFF",
    magenta: "#FF6F98",
    cyan: "#4FD8EA",
    white: "#F2EAD3",
    brightBlack: "#9F95C8",
    brightRed: "#FF8A78",
    brightGreen: "#9EF0A0",
    brightYellow: "#FFE6B0",
    brightBlue: "#8ADBFF",
    brightMagenta: "#FF6F98",
    brightCyan: "#4FD8EA",
    brightWhite: "#FFFFFF",
  };
  const TERMINAL_LOOKS = {
    light: { fontFamily: TERMINAL_FONT, fontSize: TERMINAL_SIZE, theme: CRT },
    dark: { fontFamily: TERMINAL_FONT, fontSize: TERMINAL_SIZE, theme: CRT },
  };
  const VIEWS = {
    home: (ctx) => StarMap.create(ctx),
    level: (ctx, route) => LevelScreen.create(ctx, route.id),
    guide: (ctx) => FieldGuide.create(ctx),
    cards: (ctx, route) => CardsView.create(ctx, route.chapter),
    notes: (ctx, route) => NotesView.create(ctx, route.chapter),
    dev: (ctx) => DevList.create(ctx),
    playground: (ctx, route) => PlaygroundScreen.create(ctx, route),
  };
  const OWN_HEAD = ["home", "level", "guide", "playground"];

  /* client.js removes the fragment when it carries the access key; keep the address part first. */
  const firstAddress = Route.address(location.hash);
  const app = { status: null, view: null, turn: 0, terminal: null, terminalFor: null, locked: false, fromLevel: null };
  const client = createClient({ header: "X-FirstCommit-Token", storageKey: "firstcommit.token", command: "firstcommit", onLocked: () => showLocked() });
  const game = createGameApi(client.api);
  const main = document.getElementById("app");
  const darkScheme = window.matchMedia("(prefers-color-scheme: dark)");

  function readStored(key) {
    try {
      return localStorage.getItem(key);
    } catch (error) {
      return null; /* Storage is blocked: the defaults hold for this visit. */
    }
  }

  function store(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch (error) {
      /* Storage is blocked: the choice lasts for this visit. */
    }
  }

  let themeChoice = THEMES.includes(readStored(THEME_KEY)) ? readStored(THEME_KEY) : "auto";
  const shownTheme = () => (themeChoice === "auto" ? (darkScheme.matches ? "dark" : "light") : themeChoice);

  function applyTheme() {
    document.documentElement.dataset.theme = shownTheme();
    for (const button of document.querySelectorAll(".pref-theme")) button.textContent = t(`pref.theme.${themeChoice}`);
    if (app.terminal) app.terminal.setLook(shownTheme(), t("terminal.title"));
    for (const person of ["you", "alex"]) if (play[person]) play[person].setLook(shownTheme(), t(`pg.term.${person}`));
  }

  function cycleTheme() {
    themeChoice = THEMES[(THEMES.indexOf(themeChoice) + 1) % THEMES.length];
    store(THEME_KEY, themeChoice);
    applyTheme();
  }

  function renderSound() {
    for (const button of document.querySelectorAll(".pref-sound")) {
      button.textContent = t(Sound.isEnabled() ? "pref.sound.on" : "pref.sound.off");
      button.setAttribute("aria-pressed", String(Sound.isEnabled()));
    }
  }

  function toggleSound() {
    Sound.setEnabled(!Sound.isEnabled());
    renderSound();
  }

  /* The words of the terminal's status and its hide/show button, in the page's language. */
  const terminalLabels = () => Object.fromEntries(["connecting", "connected", "hide", "show", "hint"].map((name) => [name, t(`terminal.${name}`)]));

  /* The page's own words, in the game's language (Status.language); English until the game
     first answers. */
  function applyLanguage(language) {
    Strings.use(language);
    document.documentElement.lang = Strings.language();
    for (const node of document.querySelectorAll("[data-text]")) node.textContent = t(node.dataset.text);
    for (const button of document.querySelectorAll(".pref-theme")) button.title = t("pref.theme.tip");
    for (const button of document.querySelectorAll(".pref-sound")) button.title = t("pref.sound.tip");
    for (const button of document.querySelectorAll(".pref-language")) {
      button.textContent = t("pref.language");
      button.title = t("pref.language.tip");
    }
    applyTheme();
    renderSound();
    for (const shell of [app.terminal, play.you, play.alex]) if (shell) shell.setLabels(terminalLabels());
  }

  async function switchLanguage() {
    const language = Strings.language() === "es" ? "en" : "es";
    await game.language(language);
    show(Route.parse(location.hash));
  }

  /* New look, sound and language buttons, for a view's own bar. */
  const prefButtons = () => [
    el("button", { type: "button", class: "btn btn-quiet pref pref-theme", title: t("pref.theme.tip"), onclick: cycleTheme }, t(`pref.theme.${themeChoice}`)),
    el("button", { type: "button", class: "btn btn-quiet pref pref-sound", title: t("pref.sound.tip"), "aria-pressed": String(Sound.isEnabled()), onclick: toggleSound }, t(Sound.isEnabled() ? "pref.sound.on" : "pref.sound.off")),
    el("button", { type: "button", class: "btn btn-quiet pref pref-language", lang: Strings.language() === "es" ? "en" : "es", title: t("pref.language.tip"), onclick: switchLanguage }, t("pref.language")),
  ];

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
    badge.setAttribute("aria-label", t("nav.due", { count: status.cards_due }));
  }

  function toast(message) {
    const item = el("div", { class: "toast", role: "alert" },
      el("p", {}, message),
      el("button", { type: "button", class: "link-button", onclick: () => item.remove() }, t("toast.dismiss")),
    );
    document.querySelector(".toasts").append(item);
    setTimeout(() => item.remove(), TOAST_MS);
  }

  /* A 500 says its kind in the reply: "save" for a damaged save file. Anything else, a 500
     without a kind included, is a bug, which starting over would not fix. */
  const damagedSave = (error) => error.status === 500 && Boolean(error.data) && error.data.kind === "save";

  /* The last resort for errors no view handled. */
  function report(error) {
    if (app.locked || (error && error.status === 403)) return;
    const status = error ? error.status : undefined;
    const detail = error && error.message ? error.message : String(error);
    let message = t("error.any", { detail });
    if (status === 0) message = t("error.down");
    else if (damagedSave(error)) message = t("error.damaged", { detail });
    else if (status === 500) message = t("error.bug", { detail });
    toast(message);
  }

  /* A paragraph whose commands, between backticks in the string, show as code. */
  const say = (key) => el("p", {}, Strings.parts(key).map((part) => (typeof part === "string" ? part : el("code", {}, part.code))));

  function showScreen(title, ...body) {
    if (app.view && app.view.dispose) app.view.dispose();
    app.view = null;
    main.replaceChildren(el("section", { class: "panel narrow fatal" }, el("h1", {}, title), ...body));
  }

  function showLocked() {
    showScreen(t("locked.title"), say("locked.why"), say("locked.how"));
    app.locked = true;
  }

  async function startOver() {
    const sure = await Dialog.confirm({
      title: t("restart.title"),
      text: t("restart.text"),
      confirm: t("restart.confirm"),
      cancel: t("restart.cancel"),
      danger: true,
    });
    if (!sure) return;
    await game.reset();
    show(Route.parse(location.hash));
  }

  function showBug(message) {
    showScreen(t("bug.title"),
      el("p", {}, message),
      el("p", {}, `${t("error.details")} ${t("bug.retry")}`),
      el("div", { class: "actions" }, el("button", { type: "button", class: "btn btn-primary", onclick: () => show(Route.parse(location.hash)) }, t("bug.again"))),
    );
  }

  function showDamaged(message) {
    showScreen(t("damaged.title"),
      el("p", {}, message),
      say("damaged.why"),
      el("div", { class: "actions" }, el("button", { type: "button", class: "btn btn-danger start-over", onclick: startOver }, t("restart.confirm"))),
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
        app.terminal = createTerminal({ protocol: "firstcommit", token: client.token, command: "firstcommit", looks: TERMINAL_LOOKS, labels: terminalLabels(), storagePrefix: "firstcommit.", openFromHeight: 0, onUnreachable: probe });
        app.terminalFor = key;
        app.terminal.setLook(shownTheme(), t("terminal.title"));
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
    run: (line) => app.terminal && app.terminal.run(line),
  };

  /* The playground's two shells, yours and Alex's, each on its own endpoint: they live while the
     start they were opened for stands, even while the player is elsewhere, and are replaced when
     it is built again. */
  const PLAY_PATHS = { you: "/api/terminal/playground", alex: "/api/terminal/playground-alex" };
  const play = { you: null, alex: null, started: null, titles: {}, listeners: {} };

  function disposePlay() {
    for (const person of ["you", "alex"]) {
      if (play[person]) play[person].dispose();
      play[person] = null;
      play.titles[person] = "";
    }
  }

  /* A shell's title (the editor wrappers set it) goes to the playground showing it; one set while
     the player was away is told when it is shown again. */
  function retitle(person, title) {
    play.titles[person] = title;
    if (play.listeners[person]) play.listeners[person](title);
  }

  const playTerminals = {
    attach(person, host, started, onTitle) {
      if (play.started !== started) disposePlay();
      play.started = started;
      if (!play[person]) {
        play[person] = createTerminal({ protocol: "firstcommit", token: client.token, command: "firstcommit", path: PLAY_PATHS[person], looks: TERMINAL_LOOKS, labels: terminalLabels(), storagePrefix: `firstcommit.pg-${person}.`, openFromHeight: 0, onUnreachable: probe, onTitle: (title) => retitle(person, title) });
        play[person].setLook(shownTheme(), t(`pg.term.${person}`));
      }
      play.listeners[person] = onTitle;
      if (play.titles[person]) onTitle(play.titles[person]);
      host.append(play[person].element);
      play[person].start();
    },
    detach() {
      play.listeners = {};
      for (const person of ["you", "alex"]) if (play[person]) play[person].element.remove();
    },
    type: (person, text) => play[person] && play[person].type(text),
    keys: (person, keys) => play[person] && play[person].keys(keys),
  };

  /* A refused WebSocket looks like a network failure; asking the API tells a stale key apart
     (client.js then shows the locked screen). Its own failure is already shown in the terminal. */
  function probe() {
    game.status().catch(() => null);
  }

  async function refresh() {
    app.status = await game.status();
    if (app.status.language !== Strings.language()) applyLanguage(app.status.language);
    renderHeader();
    return app.status;
  }

  const ctx = {
    game,
    status: () => app.status,
    refresh,
    reload: () => show(Route.parse(location.hash)),
    sound: Sound,
    timers: window,
    page: document,
    prefButtons,
    reducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    terminal,
    playTerminals,
    /* The level the player came to the playground from (a field guide card over it), or null. */
    back: () => app.fromLevel,
  };

  /* Remembers the level being left for the playground, so it can lead back; any other view forgets it. */
  function noteLevel(route) {
    if (route.view === "level") app.fromLevel = route.id;
    else if (route.view !== "playground") app.fromLevel = null;
  }

  /* Shows the view for an address; a newer navigation that starts while this one waits wins. */
  async function show(route) {
    if (app.locked) return;
    if (app.view && app.view.dispose) app.view.dispose();
    app.view = null;
    app.turn += 1;
    noteLevel(route);
    const turn = app.turn;
    try {
      await refresh();
    } catch (error) {
      if (error.status === 0) showScreen(t("unreachable.title"), say("unreachable.text"));
      else if (damagedSave(error)) showDamaged(error.message);
      else if (error.status === 500) showBug(error.message);
      else if (error.status !== 403) throw error;
      return;
    }
    if (turn !== app.turn) return;
    app.view = VIEWS[route.view](ctx, route);
    main.replaceChildren(app.view.element);
    document.querySelector(".topbar").hidden = OWN_HEAD.includes(route.view);
    document.title = `${t(`view.${route.view}`)} · ${t("app.title")}`;
    for (const link of document.querySelectorAll(".nav a")) link.toggleAttribute("aria-current", link.dataset.view === route.view);
    main.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }

  /* Tab completes in the shell; Shift+Tab leaves the terminal, so the keyboard is never trapped. */
  function releaseTerminalFocus(event) {
    if (event.key === "Tab" && event.shiftKey && event.target.closest && event.target.closest(".term-host")) event.stopPropagation();
  }

  function boot() {
    document.body.prepend(ArtSky.dust("first-commit"));
    applyLanguage("en");
    darkScheme.addEventListener("change", applyTheme);
    document.querySelector(".pref-theme").addEventListener("click", cycleTheme);
    document.querySelector(".pref-sound").addEventListener("click", toggleSound);
    document.querySelector(".pref-language").addEventListener("click", switchLanguage);
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
