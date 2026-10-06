"use strict";

/*
 * A modal question with two answers, on the browser's own <dialog> (it traps focus and closes
 * on Escape). Needs dom.js. Defines one global, Dialog.
 */

/* global Dom */
/* exported Dialog */

const Dialog = (function () {
  const { el } = Dom;

  /* Asks; resolves true when the player confirms, false when they cancel or press Escape.
     Focus starts on the cancel button, so Enter never confirms by accident. */
  function confirm({ title, text, confirm: confirmLabel, cancel: cancelLabel, danger = false }) {
    return new Promise((resolve) => {
      const cancelButton = el("button", { type: "button", class: "btn btn-ghost is-cancel", onclick: () => dialog.close("cancel") }, cancelLabel);
      const confirmButton = el("button", { type: "button", class: `btn ${danger ? "btn-danger" : "btn-primary"} is-confirm`, onclick: () => dialog.close("confirm") }, confirmLabel);
      const dialog = el("dialog", { class: "dialog", "aria-labelledby": "dialog-title" },
        el("h2", { id: "dialog-title" }, title),
        text && el("p", {}, text),
        el("div", { class: "actions" }, cancelButton, confirmButton),
      );
      dialog.addEventListener("close", () => {
        dialog.remove();
        resolve(dialog.returnValue === "confirm");
      });
      document.body.append(dialog);
      dialog.showModal();
      cancelButton.focus();
    });
  }

  return { confirm };
})();
