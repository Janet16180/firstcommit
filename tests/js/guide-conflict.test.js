"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { makeEvent } = require("./fakedom");
const { installBrowser, load } = require("./load");

const document = installBrowser();
const { GuideConflict, GuideGit, GuideText } = load(["dom.js", "strings.js", "places.js", "chain.js", "guide-pictures.js", "guide-card.js", "guide-git.js", "guide-text.js", "guide-conflict.js"], ["GuideConflict", "GuideGit", "GuideText"]);

/* GuideText's {en, es} pairs in one language, as the field guide passes them. */
function localized(value, language) {
  if (typeof value !== "object") return value;
  if (Array.isArray(value)) return value.map((item) => localized(item, language));
  if ("en" in value) return value[language];
  return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, localized(item, language)]));
}

function create(language = "en") {
  const view = GuideConflict.create(GuideGit, localized(GuideText.conflict, language));
  document.body.replaceChildren(view.element);
  return view.element;
}

const fileLines = (section) => [...section.querySelector(".gx-file--marked").querySelectorAll("li")];
const lineOf = (section, text) => fileLines(section).find((li) => li.firstChild.data === text || li.textContent.startsWith(text));
const explainTitle = (section) => section.querySelector(".gx-explain h3").textContent;
const next = (section) => section.querySelector(".gx-next");
const step = (section, count) => {
  for (let at = 0; at < count; at += 1) next(section).click();
};

test("the conflict opens on the real file git wrote, markers and all, at step 1 of 7", () => {
  const section = create();
  assert.equal(section.querySelector("h2").textContent, "When a merge stops: a conflict");
  assert.equal(section.querySelector(".gx-count").textContent, "Step 1 of 7");
  const texts = fileLines(section).map((li) => li.firstChild.data);
  assert.deepEqual(texts, GuideGit.conflict.markers.replace(/\n$/, "").split("\n"));
  assert.match(section.querySelector(".gc-term").textContent, /CONFLICT \(content\): Merge conflict in checklist\.txt/);
});

test("the first time git says \"both modified\", one line says what it means", () => {
  assert.match(create().textContent, /"both modified" is git status's word for this file/);
});

test("the add step says plainly what git add does in a conflict", () => {
  const section = create();
  step(section, 4);
  [...section.querySelectorAll(".gx-keep button")][0].click();
  step(section, 1);
  assert.equal(section.querySelector(".gx-sentence").textContent, "git add tells Git this file is resolved: git add checklist.txt.");
});

test("the walkthrough links to a conflict of your own in the playground", () => {
  const link = create().querySelector("a.gx-try");
  assert.equal(link.getAttribute("href"), "#/playground?start=conflict&view=conflict");
  assert.equal(link.textContent, "Try a conflict in the playground");
});

test("pointing at a part says whose it is, and leaving puts the step's picture back", () => {
  const section = create();
  assert.equal(explainTitle(section), "What Git wrote");
  const ours = lineOf(section, "4. Course: the Moon");
  ours.dispatchEvent(makeEvent("pointerenter", { pointerType: "mouse" }));
  assert.equal(explainTitle(section), "Your version");
  assert.ok(ours.classList.contains("on"));
  assert.match(ours.textContent, /You$/);
  section.querySelector(".gx-file--marked").dispatchEvent(makeEvent("pointerleave", { pointerType: "mouse" }));
  assert.equal(explainTitle(section), "What Git wrote");
});

test("focusing a line merged on its own says who changed it", () => {
  const section = create();
  lineOf(section, "6. Snack: space noodles").dispatchEvent(makeEvent("focus"));
  assert.equal(explainTitle(section), "Merged already: Alex's change");
  lineOf(section, "2. Fuel tanks: full").dispatchEvent(makeEvent("focus"));
  assert.equal(explainTitle(section), "Merged already: your change");
});

test("Next waits until a side is kept; clicking a side keeps it and shows the clean file", () => {
  const section = create();
  step(section, 4);
  assert.equal(section.querySelector(".gx-count").textContent, "Step 5 of 7");
  assert.ok(next(section).disabled);
  lineOf(section, "4. Course: Jupiter").click();
  assert.ok(!next(section).disabled);
  const clean = section.querySelector(".gx-file--clean").textContent;
  assert.match(clean, /4\. Course: Jupiter/);
  assert.doesNotMatch(clean, /<<<<<<<|=======|>>>>>>>|the Moon/);
});

test("a side can be kept from the keyboard, and both sides keep yours first", () => {
  const section = create();
  step(section, 4);
  for (const text of ["4. Course: the Moon", "4. Course: Jupiter"]) {
    const event = makeEvent("keydown", { key: "Enter" });
    lineOf(section, text).dispatchEvent(event);
    assert.ok(event.defaultPrevented);
  }
  const clean = section.querySelector(".gx-file--clean").textContent;
  assert.ok(clean.indexOf("the Moon") < clean.indexOf("Jupiter"));
  assert.match(section.textContent, /Two course lines/);
});

test("then git add settles it and git commit makes a merge commit with your commit and Alex's as parents", () => {
  const section = create();
  step(section, 4);
  [...section.querySelectorAll(".gx-keep button")][0].click();
  step(section, 1);
  assert.match(section.textContent, /All conflicts fixed but you are still merging\./);
  step(section, 1);
  const [merge, first, second] = GuideGit.conflict.head.yours.split(" ");
  const diamond = section.querySelector(".gx-diamond");
  assert.equal(diamond.getAttribute("aria-label"), `Merge commit ${merge} with parents ${first} and ${second}`);
  assert.match(section.querySelector(".gc-term").textContent, new RegExp(`\\* +${merge} Merge branch 'alex-route'`));
  assert.ok(next(section).disabled);
});

test("Back returns to the step before, and the first step has no Back", () => {
  const section = create();
  assert.ok(section.querySelector(".gx-back").disabled);
  step(section, 2);
  section.querySelector(".gx-back").click();
  assert.equal(section.querySelector(".gx-count").textContent, "Step 2 of 7");
});

test("the conflict speaks Spanish, and git's own words stay as git printed them", () => {
  const section = create("es");
  assert.equal(section.querySelector(".gx-count").textContent, "Paso 1 de 7");
  assert.equal(explainTitle(section), "Lo que escribió Git");
  assert.match(section.textContent, /Automatic merge failed/);
});
