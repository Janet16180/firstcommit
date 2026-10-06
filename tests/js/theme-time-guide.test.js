"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");

const document = installBrowser();
const { TimeGuide } = load(["dom.js", "theme-time-guide.js"], ["TimeGuide"]);

/* A storage like localStorage, or one that throws like a blocked one. */
function storage({ blocked = false, items = {} } = {}) {
  const kept = new Map(Object.entries(items));
  const refuse = () => {
    throw new Error("storage is blocked");
  };
  return blocked ? { getItem: refuse, setItem: refuse } : { getItem: (key) => kept.get(key) ?? null, setItem: (key, value) => kept.set(key, value), kept };
}

const fresh = () => {
  document.body.replaceChildren();
  return TimeGuide.create({ storage: storage() });
};

test("the guide pairs each picture with Git's word, built on the rule that the past never changes", () => {
  const titles = TimeGuide.SECTIONS.map((section) => section.title);
  for (const title of ["Save point = commit", "Timeline = branch", "Now = HEAD", "Timelines joining = merge commit", "Milestone = tag", "Shared archive = remote"]) {
    assert.ok(titles.includes(title), title);
  }
  assert.match(TimeGuide.INTRO, /the past never changes/);
});

test("the button opens the guide in a dialog that starts on its close button", () => {
  const guide = fresh();
  const button = guide.button();
  button.click();
  const dialog = document.querySelector("dialog.tt-guide");
  assert.ok(dialog.open);
  assert.equal(document.activeElement, dialog.querySelector(".tt-guide-close"));
  assert.match(dialog.textContent, /How to read the map/);
  assert.equal(dialog.querySelectorAll("h3").length, TimeGuide.SECTIONS.length);
});

test("closing the guide removes it from the page", () => {
  const guide = fresh();
  guide.button().click();
  document.querySelector(".tt-guide-close").click();
  assert.equal(document.querySelector("dialog.tt-guide"), null);
});

test("Git's words and commands in the guide are shown as code", () => {
  const guide = fresh();
  guide.button().click();
  const code = document.querySelectorAll("dialog.tt-guide code").map((node) => node.textContent);
  for (const word of ["git switch other", "origin/main", "git rebase"]) assert.ok(code.some((text) => text.includes(word)), word);
  assert.ok(!document.querySelector("dialog.tt-guide").textContent.includes("`"));
});

test("the button says it is new until the guide has been opened once, in every key on the page", () => {
  const kept = storage();
  document.body.replaceChildren();
  const guide = TimeGuide.create({ storage: kept });
  const [first, second] = [guide.button(), guide.button()];
  document.body.append(first, second);
  assert.ok(first.classList.contains("is-new") && second.classList.contains("is-new"));
  first.click();
  assert.ok(!first.classList.contains("is-new") && !second.classList.contains("is-new"));
  assert.ok(!guide.button().classList.contains("is-new"));
  assert.ok(!TimeGuide.create({ storage: kept }).button().classList.contains("is-new"), "remembered for the next visit");
});

test("with storage blocked the guide still opens, and the mark simply shows again next time", () => {
  document.body.replaceChildren();
  const guide = TimeGuide.create({ storage: storage({ blocked: true }) });
  const button = guide.button();
  assert.ok(button.classList.contains("is-new"));
  button.click();
  assert.ok(document.querySelector("dialog.tt-guide").open);
  assert.ok(TimeGuide.create({ storage: storage({ blocked: true }) }).button().classList.contains("is-new"));
});
