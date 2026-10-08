"use strict";

/*
 * The editor strip (docs/drafts/playground/plan.md, "An editor"): while nano or vim runs in a
 * playground terminal, a gold strip above it says how to save and how to quit, in that editor's
 * keys. vim's save-and-quit comes first; its other keys can fold behind "more keys" (a phone
 * folds them, orbit.css), except "Leave typing mode: Esc" while vim is typing. Ctrl+W, nano's
 * search, is never named: the browser takes it to close the tab. Get me out, in red, asks first,
 * then types the editor's quit-without-saving keys. The page learns what runs from the terminal's
 * title, which the shell's editor wrappers set. Needs dom.js, strings.js and dialog.js. Defines
 * one global, EditorStrip.
 *
 * parse(title)     {editor, path, insert} for a title "firstcommit-editor <nano|vim|vi> <args>[ insert]"
 *                  (vi is vim), else null.
 * create({onKeys, timers})
 *                  {element, show(editing)}: editing is parse()'s result, null when no editor
 *                  runs; onKeys(keys) sends keys to the terminal as typed, control keys and all.
 */

/* global Dom, Strings, Dialog */
/* exported EditorStrip */

const EditorStrip = (function () {
  const { el } = Dom;
  const { t } = Strings;
  /* engine's editor wrappers: "firstcommit-editor <nano|vim|vi> <args>", " insert" after them
     while vim types, "" once the editor exits. */
  const TITLE = /^firstcommit-editor (nano|vim|vi)\b ?(.*)$/;
  const INSERT = / insert$/;
  /* The keys each editor shows, the first never folded. */
  const KEYS = { nano: ["save", "quit"], vim: ["save", "type", "leave", "quit"] };
  /* vim leaves without saving from any mode with Esc, :q! and Enter. nano's Ctrl+X asks whether
     to save only when the file changed, so N follows only if nano still runs after NANO_ASKS_MS. */
  const VIM_QUIT = "\x1b:q!\r";
  const NANO_EXIT = "\x18";
  const NANO_NO = "n";
  const NANO_ASKS_MS = 400;

  /* The file is the one argument that is not an option; with several, all of them as typed. */
  function parse(title) {
    const match = TITLE.exec(title);
    if (!match) return null;
    const editor = match[1] === "nano" ? "nano" : "vim";
    const insert = editor === "vim" && INSERT.test(match[2]);
    const args = match[2].replace(insert ? INSERT : "", "");
    const files = args.split(/\s+/).filter((word) => word && !/^[-+]/.test(word));
    return { editor, path: files.join(" "), insert };
  }

  function create({ onKeys, timers = window }) {
    const element = el("div", { class: "pg-strip", role: "status", hidden: true });
    let current = null;

    async function getOut() {
      const { editor, path } = current;
      const sure = await Dialog.confirm({
        title: t("pg.ed.ask.title", { editor }),
        text: t("pg.ed.ask.text", { file: path }),
        confirm: t("pg.ed.ask.quit"),
        cancel: t("pg.ed.ask.keep"),
        danger: true,
      });
      if (!sure) return;
      if (editor === "vim") {
        onKeys(VIM_QUIT);
        return;
      }
      onKeys(NANO_EXIT);
      timers.setTimeout(() => current && current.editor === "nano" && onKeys(NANO_NO), NANO_ASKS_MS);
    }

    function show(editing) {
      current = editing;
      element.hidden = !editing;
      if (!editing) return;
      const { editor, insert } = editing;
      const items = KEYS[editor].map((name, at) => {
        const classes = ["pg-strip-key", at > 0 && editor === "vim" && "is-more", insert && name === "leave" && "is-always"].filter(Boolean);
        return el("li", { class: classes.join(" ") }, t(`pg.ed.${editor}.${name}`));
      });
      const toggle = editor === "vim" ? el("button", { type: "button", class: "pg-strip-toggle", "aria-expanded": String(element.classList.contains("is-open")), onclick: () => {
        toggle.setAttribute("aria-expanded", String(element.classList.toggle("is-open")));
      } }, t("pg.ed.more")) : null;
      element.dataset.editor = editor;
      element.replaceChildren(...[
        el("b", { class: "pg-strip-name" }, editor),
        el("ul", { class: "pg-strip-keys" }, items),
        toggle,
        el("button", { type: "button", class: "btn btn-danger pg-strip-out", onclick: getOut }, t("pg.ed.out")),
      ].filter(Boolean));
    }

    return { element, show };
  }

  return { parse, create };
})();
