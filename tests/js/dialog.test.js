"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load, settle } = require("./load");

const document = installBrowser();
const { Dialog } = load(["dom.js", "dialog.js"], ["Dialog"]);

test("confirming resolves true and removes the dialog", async () => {
  const answer = Dialog.confirm({ title: "Leave this level?", text: "Your lab is deleted.", confirm: "Leave", cancel: "Stay" });
  const dialog = document.body.querySelector("dialog");
  assert.ok(dialog.hasAttribute("open"));
  assert.match(dialog.textContent, /Leave this level\?.*Your lab is deleted\./);
  assert.equal(document.activeElement.textContent, "Stay");
  dialog.querySelector("button.is-confirm").click();
  assert.equal(await answer, true);
  assert.equal(document.body.querySelector("dialog"), null);
});

test("cancelling, or closing with Escape, resolves false", async () => {
  const cancelled = Dialog.confirm({ title: "Erase?", text: "", confirm: "Erase", cancel: "Keep" });
  document.body.querySelector("button.is-cancel").click();
  assert.equal(await cancelled, false);
  const escaped = Dialog.confirm({ title: "Erase?", text: "", confirm: "Erase", cancel: "Keep" });
  document.body.querySelector("dialog").close();
  await settle();
  assert.equal(await escaped, false);
});

test("a dangerous action is styled as one", () => {
  Dialog.confirm({ title: "Erase?", text: "", confirm: "Erase", cancel: "Keep", danger: true });
  assert.ok(document.body.querySelector("button.is-confirm").classList.contains("btn-danger"));
  document.body.querySelector("dialog").close();
});
