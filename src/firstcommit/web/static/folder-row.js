"use strict";

/*
 * The folder row (docs/drafts/sector5/5-3): the files in your working folder, in a row under the
 * chain, so a switch shows its effect on the folder: a file that left stays struck through and one
 * that came is marked new, until the folder's files change again. Files Git ignores are left out.
 * Needs dom.js and strings.js. Defines one global, FolderRow.
 *
 * create() {element, update(files)}: the row, from a snapshot's files.
 */

/* global Dom, Strings */
/* exported FolderRow */

const FolderRow = (function () {
  const { el } = Dom;
  const { t } = Strings;

  function create() {
    const element = el("div", { class: "folder-row" });
    let shown = null;
    let came = [];
    let left = [];

    function update(files) {
      const now = files.filter((file) => file.folder !== null && !file.ignored).map((file) => file.path);
      const changed = shown !== null && (now.length !== shown.length || now.some((path) => !shown.includes(path)));
      if (changed) {
        came = now.filter((path) => !shown.includes(path));
        left = shown.filter((path) => !now.includes(path));
      }
      shown = now;
      const chip = (path, kind) => el("span", { class: kind ? `folder-file ${kind}` : "folder-file" }, path);
      element.replaceChildren(
        el("b", { class: "folder-name" }, t("folder.label")),
        ...now.map((path) => chip(path, came.includes(path) ? "is-new" : "")),
        ...left.map((path) => chip(path, "is-gone")));
    }

    return { element, update };
  }

  return { create };
})();
