"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { html } = require("./fakedom");
const { createClock, installBrowser, load } = require("./load");
const { STYLE, assertPalette, assertStyled, colours, labelOf, walk } = require("./art-check");

installBrowser();
const { ArtMoments } = load(["dom.js", "art-pixels.js", "art-moments.js"], ["ArtMoments"]);

const WHAT_IF = { whatIf: "WHAT IF" };
const ENGLISH = {
  "secret-leak": { ...WHAT_IF, keys: "keys.txt", mothership: "origin", caption: "Everyone who can see the repository can read it, in every copy, forever." },
  launch: { nav: "nav.cfg", engine: "engine.cfg", caption: "Two people, at the same time, on different parts: Git put the pieces together." },
  "junk-flood": { ...WHAT_IF, command: "git add .", caption: "The build files would ride along to every copy." },
  "unreviewed-main": { ...WHAT_IF, caption: "Unreviewed work would land on everyone's main." },
  "force-break": { ...WHAT_IF, command: "git push --force", caption: "Alex's commit would be gone from the mothership." },
  "search-beam": { ...WHAT_IF, caption: "Git never saved that edit, so there is nothing to find." },
};
const SI = { whatIf: "¿Y SI…?" };
const SPANISH = {
  "secret-leak": { ...ENGLISH["secret-leak"], ...SI, caption: "Todos los que pueden ver el repositorio pueden leerlo, en cada copia, para siempre." },
  launch: { ...ENGLISH.launch, caption: "Dos personas, al mismo tiempo, en partes distintas: Git juntó las piezas." },
  "junk-flood": { ...ENGLISH["junk-flood"], ...SI, caption: "Los archivos de compilación viajarían a cada copia." },
  "unreviewed-main": { ...SI, caption: "Trabajo sin revisar llegaría al main de todos." },
  "force-break": { ...ENGLISH["force-break"], ...SI, caption: "El commit de Alex desaparecería de la nave nodriza." },
  "search-beam": { ...SI, caption: "Git nunca guardó esa edición, así que no hay nada que encontrar." },
};
const WHAT_IFS = ["secret-leak", "junk-flood", "unreviewed-main", "force-break", "search-beam"];

const wordsOf = (element) => [...walk(element)].filter((node) => node.localName === "text").map((node) => node.textContent);
const classesOf = (element) => [...walk(element)].flatMap((node) => node.classList.list());
const moving = (element) => classesOf(element).filter((name) => /^art-(wi|launch)-/.test(name) || name === "art-alarm" || name === "art-flick");
const play = (name, options = {}) => ArtMoments.play(name, { captions: ENGLISH[name], ...options }).element;

test("the moments are the leak, the launch and the four what-ifs of wave 2, each listing its captions", () => {
  assert.deepEqual([...ArtMoments.NAMES], ["secret-leak", "launch", "junk-flood", "unreviewed-main", "force-break", "search-beam"]);
  assert.deepEqual(Object.keys(ArtMoments.CAPTIONS), [...ArtMoments.NAMES]);
  for (const name of ArtMoments.NAMES) assert.deepEqual([...ArtMoments.CAPTIONS[name]], Object.keys(ENGLISH[name]), name);
});

test("every word a moment draws is one of its captions, in drawing order, and the caption names it", () => {
  for (const name of ArtMoments.NAMES) {
    const marked = Object.fromEntries(ArtMoments.CAPTIONS[name].map((key) => [key, `<${key}>`]));
    for (const reducedMotion of [false, true]) {
      const { element } = ArtMoments.play(name, { captions: marked, reducedMotion });
      assert.deepEqual(wordsOf(element), Object.values(marked), name);
      assert.equal(labelOf(element), "<caption>");
    }
  }
});

test("a moment is a picture in tokens and styled classes that fills the layer it is put in", () => {
  for (const name of ArtMoments.NAMES) {
    const element = play(name);
    assert.equal(element.getAttribute("viewBox"), "0 0 400 100");
    assert.equal(element.getAttribute("width"), "100%");
    assert.equal(element.getAttribute("height"), "100%");
    assert.equal(element.getAttribute("preserveAspectRatio"), "xMidYMid meet");
    assert.ok(element.classList.contains("art-moment"));
    assertPalette(element);
    assertStyled(element);
    assert.equal(html(element), html(play(name)), `${name} is drawn the same each time`);
  }
});

test("the what-if moments play in greyscale under their heading; the launch is real and in colour", () => {
  for (const name of WHAT_IFS) {
    const element = play(name);
    assert.ok(element.classList.contains("art-moment--whatif"), name);
    assert.equal(wordsOf(element)[0], "WHAT IF", name);
    assert.match(element.getAttribute("style"), /--art-moment:7s/, name);
  }
  assert.ok(!play("launch").classList.contains("art-moment--whatif"));
  assert.match(STYLE, /\.art-moment--whatif \{[^}]*filter: grayscale\(1\)/);
});

test("the secret leak seals the keys, sends them up and out to four crew stations, then rewinds", () => {
  const element = play("secret-leak");
  for (const part of ["art-wi-sweep", "art-wi-rise", "art-wi-land", "art-wi-glow", "art-wi-caption"]) assert.ok(classesOf(element).includes(part), part);
  assert.equal(element.querySelectorAll(".art-wi-land").length, 4);
});

test("the junk flood sweeps the build crates onto the dock and out to four crew stations", () => {
  const element = play("junk-flood");
  for (const part of ["art-wi-sweep", "art-wi-rise", "art-wi-land", "art-wi-caption"]) assert.ok(classesOf(element).includes(part), part);
  assert.equal(element.querySelectorAll(".art-wi-land").length, 4);
});

test("unreviewed work rises onto the mothership's line and lands at Alex's station", () => {
  const element = play("unreviewed-main");
  assert.equal(element.querySelectorAll(".art-wi-rise").length, 1);
  assert.equal(element.querySelectorAll(".art-wi-land").length, 1);
  assert.ok(element.querySelector("rect[fill=\"var(--art-green)\"]"), "Alex's station");
});

test("a forced push replaces Alex's capsule, which cracks and falls off the line", () => {
  const element = play("force-break");
  for (const part of ["art-wi-rise", "art-wi-fall", "art-wi-crack"]) assert.ok(classesOf(element).includes(part), part);
  const fallen = element.querySelector(".art-wi-fall");
  assert.ok(fallen.querySelector("rect[fill=\"var(--art-green)\"]"), "Alex's capsule falls");
  assert.ok(fallen.querySelector(".art-wi-crack"), "and it is the one that cracks");
});

test("the search beam sweeps the black box, the workshop outside it, and finds nothing", () => {
  const element = play("search-beam");
  for (const part of ["art-wi-beam", "art-wi-mark", "art-wi-caption"]) assert.ok(classesOf(element).includes(part), part);
  const box = element.querySelector("rect[stroke=\"var(--art-orange)\"][stroke-width=\"2\"]");
  const workshop = element.querySelector("rect[stroke=\"var(--art-orange)\"][stroke-width=\"1\"]");
  assert.ok(box && workshop);
  assert.ok(Number(workshop.getAttribute("x")) + Number(workshop.getAttribute("width")) < Number(box.getAttribute("x")), "the workshop stays outside the box");
});

test("the launch joins the two halves into one ship and sends it up", () => {
  const element = play("launch");
  for (const part of ["art-launch-join", "art-launch-ship", "art-launch-flame", "art-launch-caption"]) assert.ok(classesOf(element).includes(part), part);
  assert.equal(element.querySelectorAll(".art-launch-join").length, 2);
  assert.match(element.getAttribute("style"), /--art-moment:5s/);
});

test("under reduced motion a moment is its still frame: nothing moves, the caption shows", () => {
  for (const name of ArtMoments.NAMES) {
    const element = play(name, { reducedMotion: true });
    assert.deepEqual(moving(element), [], name);
    assert.ok(wordsOf(element).includes(ENGLISH[name].caption), name);
  }
  assert.equal(play("secret-leak", { reducedMotion: true }).querySelectorAll(".art-wi-sweep").length, 0);
});

test("the moments' animations live in the art sheet, timed by --art-moment, and stop under reduced motion", () => {
  const parts = ["art-wi-sweep", "art-wi-rise", "art-wi-land", "art-wi-glow", "art-wi-crack", "art-wi-fall", "art-wi-beam", "art-wi-mark", "art-wi-caption", "art-launch-join", "art-launch-ship", "art-launch-flame", "art-launch-ring", "art-launch-caption"];
  for (const name of parts) assert.match(STYLE, new RegExp(`\\.${name} \\{[^}]*animation: ${name} var\\(--art-moment\\) steps\\(\\d+\\) both;`), name);
  const reduced = STYLE.slice(STYLE.indexOf("@media (prefers-reduced-motion: reduce)"));
  assert.match(reduced, /\.art-moment \*/);
  assert.match(STYLE, /\.art-moment \{[^}]*background: var\(--void\)/);
});

test("finished resolves once the moment has played, still or moving, on the timers it is given", async () => {
  for (const [name, reducedMotion, ms] of [["secret-leak", false, 7000], ["launch", true, 5000], ["search-beam", false, 7000]]) {
    const clock = createClock();
    let done = false;
    ArtMoments.play(name, { captions: ENGLISH[name], reducedMotion, timers: clock }).finished.then(() => { done = true; });
    await clock.advance(ms - 1);
    assert.equal(done, false, name);
    await clock.advance(1);
    assert.equal(done, true, name);
  }
});

test("the Spanish captions draw too, and a missing caption or an unknown moment is refused", () => {
  for (const name of ArtMoments.NAMES) assert.ok(wordsOf(ArtMoments.play(name, { captions: SPANISH[name] }).element).some((line) => SPANISH[name].caption.startsWith(line)), name);
  assert.throws(() => ArtMoments.play("launch", { captions: { nav: "nav.cfg", caption: "x" } }), (error) => error instanceof RangeError && /launch/.test(error.message) && /engine/.test(error.message));
  assert.throws(() => ArtMoments.play("force-break", { captions: { command: "x", caption: "x" } }), (error) => error instanceof RangeError && /force-break/.test(error.message) && /whatIf/.test(error.message));
  assert.throws(() => ArtMoments.play("eclipse", { captions: {} }), RangeError);
});

test("a long caption breaks onto two lines at a space near its middle", () => {
  const long = "word ".repeat(30).trim();
  const lines = wordsOf(ArtMoments.play("launch", { captions: { ...ENGLISH.launch, caption: long } }).element).filter((line) => line.startsWith("word"));
  assert.equal(lines.length, 2);
  assert.equal(lines.join(" "), long);
  assert.ok(Math.abs(lines[0].length - lines[1].length) <= 5);
});

test("the stations' flag poles show against the night", () => {
  const element = play("launch");
  const domes = [...walk(element)].filter((node) => /scale\(2\)$/.test(node.getAttribute("transform") || "") && node.querySelector("rect[fill=\"var(--art-yellow)\"]"));
  assert.equal(domes.length, 2);
  for (const dome of domes) assert.ok(dome.querySelector("rect[fill=\"var(--star)\"]"));
});

test("in the launch, your half is violet and Alex's half green, with no pink", () => {
  const painted = new Set(colours(play("launch")));
  for (const tone of ["art-violet", "art-violet-lt", "art-green", "art-green-lt"]) assert.ok(painted.has(`var(--${tone})`), tone);
  assert.ok(![...painted].some((colour) => colour.startsWith("var(--art-pink")));
});
