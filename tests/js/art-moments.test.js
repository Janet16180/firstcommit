"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { html } = require("./fakedom");
const { installBrowser, load } = require("./load");
const { STYLE, assertPalette, assertStyled, labelOf, walk } = require("./art-check");

installBrowser();
const { ArtMoments } = load(["dom.js", "art-pixels.js", "art-moments.js"], ["ArtMoments"]);

const ENGLISH = {
  "secret-leak": { keys: "keys.txt", mothership: "origin", caption: "Everyone who can see the repository can read it, in every copy, forever." },
  launch: { nav: "nav.cfg", engine: "engine.cfg", caption: "Two people, at the same time, on different parts: Git put the pieces together." },
};
const SPANISH = {
  "secret-leak": { ...ENGLISH["secret-leak"], caption: "Todos los que pueden ver el repositorio pueden leerlo, en cada copia, para siempre." },
  launch: { ...ENGLISH.launch, caption: "Dos personas, al mismo tiempo, en partes distintas: Git juntó las piezas." },
};

const wordsOf = (element) => [...walk(element)].filter((node) => node.localName === "text").map((node) => node.textContent);
const classesOf = (element) => [...walk(element)].flatMap((node) => node.classList.list());
const moving = (element) => classesOf(element).filter((name) => /^art-(leak|launch)-/.test(name) || name === "art-alarm" || name === "art-flick");

test("there are two moments, each listing the captions it draws in drawing order", () => {
  assert.deepEqual([...ArtMoments.NAMES], ["secret-leak", "launch"]);
  assert.deepEqual(Object.keys(ArtMoments.CAPTIONS), [...ArtMoments.NAMES]);
  for (const name of ArtMoments.NAMES) assert.deepEqual([...ArtMoments.CAPTIONS[name]], Object.keys(ENGLISH[name]), name);
});

test("every word a moment draws comes from its captions, and the caption names the picture", () => {
  for (const name of ArtMoments.NAMES) {
    const marked = Object.fromEntries(ArtMoments.CAPTIONS[name].map((key) => [key, `<${key}>`]));
    for (const reducedMotion of [false, true]) {
      const { element } = ArtMoments.play(name, { captions: marked, reducedMotion });
      assert.deepEqual(new Set(wordsOf(element)), new Set(Object.values(marked)), name);
      assert.equal(labelOf(element), "<caption>");
    }
  }
});

test("a moment is a picture in tokens and styled classes that fills the layer it is put in", () => {
  for (const name of ArtMoments.NAMES) {
    const { element } = ArtMoments.play(name, { captions: ENGLISH[name] });
    assert.equal(element.getAttribute("viewBox"), "0 0 400 100");
    assert.equal(element.getAttribute("width"), "100%");
    assert.equal(element.getAttribute("height"), "100%");
    assert.equal(element.getAttribute("preserveAspectRatio"), "xMidYMid meet");
    assert.ok(element.classList.contains("art-moment"));
    assertPalette(element);
    assertStyled(element);
    assert.equal(html(element), html(ArtMoments.play(name, { captions: ENGLISH[name] }).element), `${name} is drawn the same each time`);
  }
});

test("the secret leak seals the keys, sends them up and out to four crew stations, then rewinds", () => {
  const { element } = ArtMoments.play("secret-leak", { captions: ENGLISH["secret-leak"] });
  const classes = classesOf(element);
  for (const part of ["art-leak-file", "art-leak-ghost", "art-leak-copy", "art-leak-glow", "art-leak-caption"]) assert.ok(classes.includes(part), part);
  assert.equal(element.querySelectorAll(".art-leak-copy").length, 4);
  assert.match(element.getAttribute("style"), /--art-moment:7s/);
});

test("the launch joins the two halves into one ship and sends it up", () => {
  const { element } = ArtMoments.play("launch", { captions: ENGLISH.launch });
  const classes = classesOf(element);
  for (const part of ["art-launch-join", "art-launch-ship", "art-launch-flame", "art-launch-caption"]) assert.ok(classes.includes(part), part);
  assert.equal(element.querySelectorAll(".art-launch-join").length, 2);
  assert.match(element.getAttribute("style"), /--art-moment:5s/);
});

test("under reduced motion a moment is its still frame: nothing moves, the caption shows", () => {
  for (const name of ArtMoments.NAMES) {
    const { element } = ArtMoments.play(name, { captions: ENGLISH[name], reducedMotion: true });
    assert.deepEqual(moving(element), [], name);
    assert.ok(wordsOf(element).includes(ENGLISH[name].caption), name);
  }
  const still = ArtMoments.play("secret-leak", { captions: ENGLISH["secret-leak"], reducedMotion: true }).element;
  assert.equal(still.querySelectorAll(".art-leak-file").length, 0, "the keys are already sealed and away");
});

test("the moment's animations live in the art sheet, timed by --art-moment, and stop under reduced motion", () => {
  for (const name of ["art-leak-file", "art-leak-ghost", "art-leak-copy", "art-leak-glow", "art-leak-caption", "art-launch-join", "art-launch-ship", "art-launch-flame", "art-launch-ring", "art-launch-caption"]) {
    assert.match(STYLE, new RegExp(`\\.${name} \\{\\s*animation: ${name} var\\(--art-moment\\) steps\\(\\d+\\) both;`), name);
  }
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.match(reduced, /\.art-moment \*/);
  assert.match(STYLE, /\.art-moment \{[^}]*background: var\(--void\)/);
});

test("finished resolves once the moment has played, still or moving", async (context) => {
  context.mock.timers.enable({ apis: ["setTimeout"] });
  for (const [name, reducedMotion, ms] of [["secret-leak", false, 7000], ["launch", true, 5000]]) {
    let done = false;
    ArtMoments.play(name, { captions: ENGLISH[name], reducedMotion }).finished.then(() => { done = true; });
    context.mock.timers.tick(ms - 1);
    await Promise.resolve();
    assert.equal(done, false, name);
    context.mock.timers.tick(1);
    await Promise.resolve();
    assert.equal(done, true, name);
  }
});

test("the Spanish captions draw too, and a missing caption or an unknown moment is refused", () => {
  for (const name of ArtMoments.NAMES) assert.ok(wordsOf(ArtMoments.play(name, { captions: SPANISH[name] }).element).some((line) => SPANISH[name].caption.startsWith(line)));
  assert.throws(() => ArtMoments.play("launch", { captions: { nav: "nav.cfg", caption: "x" } }), (error) => error instanceof RangeError && /launch/.test(error.message) && /engine/.test(error.message));
  assert.throws(() => ArtMoments.play("eclipse", { captions: {} }), RangeError);
});

test("a long caption breaks onto two lines at a space near its middle", () => {
  const long = "word ".repeat(30).trim();
  const lines = wordsOf(ArtMoments.play("launch", { captions: { ...ENGLISH.launch, caption: long } }).element).filter((line) => line.startsWith("word"));
  assert.equal(lines.length, 2);
  assert.equal(lines.join(" "), long);
  assert.ok(Math.abs(lines[0].length - lines[1].length) <= 5);
});
