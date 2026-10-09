"use strict";

/*
 * The game's merge tool on the page (docs/drafts/mergetool/plan.md): while `git mergetool` runs
 * the game's tool in a terminal, the click-to-keep panel (keep-panel.js) opens above that
 * terminal for the file the tool waits for, with Cancel and one footer line saying real merge
 * tools differ. The tool says it waits through the terminal's title, "firstcommit-mergetool
 * <file>", sent again every 2 s; the panel closes when the title clears or names something else,
 * when EXPIRE_MS pass without it (a tool killed without clearing it), and when the terminal's
 * connection closes. Write sends the picks (the server rewrites the file whole, and the tool,
 * seeing no markers left, ends and git adds the file); Cancel asks the terminal to cancel (the
 * caller types Ctrl-C, which the tool reads as a key). The terminal waits meanwhile, so the
 * panel offers no editor. Needs dom.js, strings.js and keep-panel.js. Defines one global, MergeTool.
 *
 * parse(title)     the file a title "firstcommit-mergetool <file>" names, else null.
 * create({timers, now, onWrite, onCancel, onOpen, onClose})
 *                  {element, title(title, at), closed(), update({person, marked, texts}), isOpen(), path()}:
 *                  title() is each title the terminal's shell sets, `at` when it came (now() when
 *                  left out, earlier for one kept while the screen was away); closed() is the
 *                  terminal's connection closing; update() the observation's files in conflict for
 *                  that person. onWrite({file, read, choices}) writes (a promise; 409 when the file
 *                  changed); onOpen(file) and onClose(why: "ended", "expired" or "terminal") tell
 *                  the screen, once each time.
 */

/* global Dom, Strings, KeepPanel */
/* exported MergeTool */

const MergeTool = (function () {
  const { el } = Dom;
  const { t } = Strings;
  const TITLE = /^firstcommit-mergetool (.+)$/;
  /* The tool sends its title every 2 s; a little over two missed sendings means it is gone. */
  const EXPIRE_MS = 5000;

  function parse(title) {
    const found = TITLE.exec(title || "");
    return found ? found[1] : null;
  }

  function create({ timers, now = () => Date.now(), onWrite, onCancel, onOpen = () => {}, onClose = () => {} }) {
    const panel = KeepPanel.create({ onWrite, onType: () => {}, chips: false, next: "tool.next" });
    const file = el("code", { class: "mtool-file" });
    const element = el("section", { class: "mtool", "aria-label": t("tool.bar"), hidden: true },
      el("p", { class: "mtool-bar" }, el("b", {}, t("tool.bar")), " ", el("code", {}, "firstcommit"), " ", file),
      el("p", { class: "mtool-wait" }, t("tool.wait")),
      panel.element,
      el("div", { class: "mtool-act" }, el("button", { type: "button", class: "btn mtool-cancel", onclick: () => onCancel() }, t("tool.cancel"))),
      el("p", { class: "mtool-foot" }, t("tool.foot")));
    const state = { path: null, expiry: null, last: null };

    function draw() {
      if (!state.path || !state.last) return;
      const { person, marked, texts } = state.last;
      panel.update({ person, marked: marked.filter((entry) => entry.path === state.path), texts, editing: null });
    }

    function close(why) {
      if (!state.path) return;
      timers.clearTimeout(state.expiry);
      state.path = null;
      element.hidden = true;
      onClose(why);
    }

    function open(path, at) {
      timers.clearTimeout(state.expiry);
      state.expiry = timers.setTimeout(() => close("expired"), at + EXPIRE_MS - now());
      if (state.path === path) return;
      state.path = path;
      file.textContent = path;
      element.hidden = false;
      draw();
      onOpen(path);
    }

    return {
      element,
      title(title, at = now()) {
        const path = parse(title);
        if (path === null) close("ended");
        else if (now() - at >= EXPIRE_MS) close("expired");
        else open(path, at);
      },
      closed: () => close("terminal"),
      update(observed) {
        state.last = observed;
        draw();
      },
      isOpen: () => state.path !== null,
      path: () => state.path,
    };
  }

  return { parse, create, EXPIRE_MS };
})();
