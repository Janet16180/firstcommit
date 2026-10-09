"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { createClock, installBrowser, load, settle } = require("./load");

const document = installBrowser();
const { ScenePlayer, ArtScenes, Strings } = load(["dom.js", "strings.js", "markup.js", "art-pixels.js", "art-sprites.js", "art-scenes.js", "scene.js"], ["ScenePlayer", "ArtScenes", "Strings"]);

const line = (art, ...spans) => ({ art, text: [{ kind: "para", spans: spans.map((span) => (Array.isArray(span) ? { text: span[0], code: true, em: false } : { text: span, code: false, em: false })) }] });
const SCENE = [line("space", "I am Rama."), line("flag", "Plant the flag with ", ["git init"], ".")];

function play({ reducedMotion = false, scene = SCENE } = {}) {
  const clock = createClock();
  let over = 0;
  ScenePlayer.play({ scene, timers: clock, reducedMotion }).then(() => (over += 1));
  const dialog = document.body.querySelector("dialog.cutscene");
  return { clock, dialog, over: () => over, q: (selector) => dialog.querySelector(selector), text: () => dialog.querySelector(".cs-txt").textContent };
}

test("a scene opens as a dialog with its first picture, Rama and a pip per line", () => {
  const run = play();
  assert.ok(run.dialog.open);
  assert.equal(run.q("svg.art-scene").dataset.scene, "space");
  assert.ok(run.q(".cs-dlg svg.art-rama"));
  assert.equal(run.dialog.querySelectorAll(".pips i").length, 2);
  assert.equal(run.q(".cs-next").textContent, "Next");
  run.q(".cs-skip").click();
});

test("each line types itself in, two characters at a time", async () => {
  const run = play();
  assert.equal(run.text(), "");
  await run.clock.advance(22);
  assert.equal(run.text(), "I ");
  await run.clock.advance(22 * 4);
  assert.equal(run.text(), "I am Rama.");
  run.q(".cs-skip").click();
});

test("Next while a line types finishes it; Next again shows the next line and its picture", async () => {
  const run = play();
  run.q(".cs-next").click();
  assert.equal(run.text(), "I am Rama.");
  run.q(".cs-next").click();
  await run.clock.advance(22 * 30);
  assert.equal(run.text(), "Plant the flag with git init.");
  assert.equal(run.q(".cs-txt code").textContent, "git init");
  assert.equal(run.q("svg.art-scene").dataset.scene, "flag");
  assert.equal(run.q(".cs-next").textContent, "Start");
  run.q(".cs-skip").click();
});

test("Next on the last line closes the scene", async () => {
  const run = play();
  for (let index = 0; index < 4; index += 1) run.q(".cs-next").click();
  await settle();
  assert.equal(run.over(), 1);
  assert.equal(document.body.querySelector("dialog.cutscene"), null);
  assert.equal(run.clock.pending(), 0);
});

test("a commit's subject in italics types in as emphasis", () => {
  const scene = [{ art: "space", text: [{ kind: "para", spans: [{ text: "Back to ", code: false, em: false }, { text: "Plot the route", code: false, em: true }] }] }];
  const run = play({ reducedMotion: true, scene });
  assert.equal(run.q(".cs-txt em").textContent, "Plot the route");
  run.q(".cs-skip").click();
});

test("Skip closes the scene at once", async () => {
  const run = play();
  run.q(".cs-skip").click();
  await settle();
  assert.equal(run.over(), 1);
  assert.equal(document.body.querySelector("dialog.cutscene"), null);
});

test("with reduced motion each line shows whole at once", () => {
  const run = play({ reducedMotion: true });
  assert.equal(run.text(), "I am Rama.");
  run.q(".cs-skip").click();
});

test("an empty scene ends at once and shows nothing", async () => {
  let over = false;
  await ScenePlayer.play({ scene: [], timers: createClock(), reducedMotion: false }).then(() => (over = true));
  assert.equal(over, true);
  assert.equal(document.body.querySelector("dialog.cutscene"), null);
});

test("the typewriter ticks while a line types, and each new line turns a page", async () => {
  const clock = createClock();
  const sounds = [];
  ScenePlayer.play({ scene: SCENE, timers: clock, reducedMotion: false, sound: { play: (name) => sounds.push(name) } });
  const dialog = document.body.querySelector("dialog.cutscene");
  await clock.advance(22 * 8);
  assert.ok(sounds.includes("type"));
  assert.equal(sounds.includes("page"), false);
  dialog.querySelector(".cs-next").click();
  dialog.querySelector(".cs-next").click();
  assert.ok(sounds.includes("page"));
  dialog.querySelector(".cs-skip").click();
});

test("every scene's label and each caption it draws are written in English and in Spanish", () => {
  const { en, es } = Strings.TABLES;
  for (const name of ArtScenes.NAMES) {
    for (const key of [`sceneLabel.${name}`, ...(ArtScenes.CAPTIONS[name] || []).map((caption) => `sceneCaption.${name}.${caption}`)]) {
      assert.ok(key in en && key in es, key);
    }
  }
  assert.deepEqual(Object.keys(ArtScenes.CAPTIONS).sort(), [...ArtScenes.NAMES].sort());
});

test("a picture's words are in the page's language", () => {
  Strings.use("es");
  try {
    const run = play({ scene: [line("planet", "Una carpeta.")] });
    assert.match(run.q("svg.art-scene").textContent, /una carpeta común/);
    assert.equal(run.q("svg.art-scene").getAttribute("aria-label"), Strings.t("sceneLabel.planet"));
    run.q(".cs-skip").click();
  } finally {
    Strings.use("en");
  }
});

test("the alarm scene opens every challenge, so its words name no one base", () => {
  for (const language of ["en", "es"]) {
    const table = Strings.TABLES[language];
    const words = Object.keys(table).filter((key) => key === "sceneLabel.alarm" || key.startsWith("sceneCaption.alarm.")).map((key) => table[key]);
    assert.deepEqual(words.filter((text) => /\d/.test(text)), [], language);
  }
});
