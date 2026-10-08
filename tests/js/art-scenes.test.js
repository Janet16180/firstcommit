"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { html } = require("./fakedom");
const { installBrowser, load } = require("./load");
const { assertPalette, assertStyled, isHidden, labelOf, walk } = require("./art-check");

installBrowser();
const { ArtScenes } = load(["dom.js", "art-pixels.js", "art-scenes.js"], ["ArtScenes"]);

/* The captions the page passes, in English and in the Spanish the scenes must fit. */
const ENGLISH = {
  space: {},
  timeline: { v1: "v1", v2: "v2", v3: "v3", v4: "v4", back: "back in time", snapshot: "every commit is a snapshot" },
  terminal: { ls: "$ ls", status: "$ git status", fatal: "fatal: not a git repository" },
  planet: { folder: "a plain folder", question: "does Git know it?" },
  flag: { init: "git init", dotgit: ".git" },
  zones: { workshop: "workshop", edit: "you edit", dock: "cargo dock", pick: "you pick", vault: "vault", keep: "you keep" },
  conveyor: { workshop: "workshop", dock: "cargo dock", title: "git add picks what goes up" },
  capsule: { vault: "vault", hash: "a1b2c3d", message: '-m "first liftoff"', commit: "git commit" },
  chain: { hash1: "a1b2c3d", message1: "liftoff", hash2: "f00d42e", message2: "Phobos stop", hash3: "9c0ffee", message3: "logbook", head: "HEAD", caption: "each capsule points to the one before" },
  orbit: { base: "your base (local)", origin: "origin" },
  rocket: { remote: "git remote add", push: "git push" },
  pull: { alex: "Alex's commit", pull: "git pull" },
  alarm: { base: "your base", alert: "alert" },
  fork: { feature: "feature", main: "main", command: "git switch -c feature" },
  merge: { main: "main", command: "git merge" },
  collision: { conflict: "CONFLICT", lines: "same file, same lines" },
  blackbox: { main: "main", reflog: "reflog" },
  meteor: { base: "base 7", alert: "alert" },
  simulator: { simulator: "jump simulator", output: "sim-output/", workshop: "workshop" },
};

const SPANISH = {
  timeline: { ...ENGLISH.timeline, back: "de vuelta al pasado", snapshot: "cada commit es una foto del proyecto" },
  planet: { folder: "una carpeta común", question: "¿Git la conoce?" },
  zones: { workshop: "taller", edit: "tú editas", dock: "muelle", pick: "tú eliges", vault: "bóveda", keep: "tú guardas" },
  conveyor: { workshop: "taller", dock: "muelle", title: "git add elige qué se carga" },
  chain: { ...ENGLISH.chain, message1: "despegue", message2: "parada en Fobos", message3: "bitácora", caption: "cada cápsula apunta a la anterior" },
  collision: { conflict: "CONFLICT", lines: "mismo archivo, mismas líneas" },
  simulator: { simulator: "simulador de saltos", output: "sim-output/", workshop: "taller" },
};

const wordsOf = (picture) => [...walk(picture)].filter((node) => node.localName === "text").map((node) => node.textContent);

test("the scenes are the design's thirteen, the four new ones of chapters 5 to 7, Base 7's meteor and Junk bay's simulator", () => {
  assert.deepEqual([...ArtScenes.NAMES], [
    "space", "timeline", "terminal", "planet", "flag", "zones", "conveyor",
    "capsule", "chain", "orbit", "rocket", "pull", "alarm",
    "fork", "merge", "collision", "blackbox", "meteor", "simulator",
  ]);
});

test("CAPTIONS lists the keys each scene draws, in drawing order", () => {
  assert.deepEqual(Object.keys(ArtScenes.CAPTIONS), [...ArtScenes.NAMES]);
  for (const name of ArtScenes.NAMES) assert.deepEqual([...ArtScenes.CAPTIONS[name]], Object.keys(ENGLISH[name]), name);
});

test("every word a scene draws is one of its captions, in order, and nothing else", () => {
  for (const name of ArtScenes.NAMES) {
    const marked = Object.fromEntries(ArtScenes.CAPTIONS[name].map((key) => [key, `<${name}.${key}>`]));
    assert.deepEqual(wordsOf(ArtScenes.scene(name, { captions: marked })), Object.values(marked), name);
  }
});

test("every scene is a picture on the 160x90 canvas, in tokens and styled classes only", () => {
  for (const name of ArtScenes.NAMES) {
    const scene = ArtScenes.scene(name, { label: name, captions: ENGLISH[name] });
    assert.equal(scene.getAttribute("viewBox"), "0 0 160 90", name);
    assertPalette(scene);
    assertStyled(scene);
    assert.equal(html(scene), html(ArtScenes.scene(name, { label: name, captions: ENGLISH[name] })), `${name} is drawn the same each time`);
  }
});

test("a scene is named by the page's label, and hidden without one", () => {
  assert.equal(labelOf(ArtScenes.scene("flag", { label: "Planting the flag", captions: ENGLISH.flag })), "Planting the flag");
  assert.ok(isHidden(ArtScenes.scene("flag", { captions: ENGLISH.flag })));
});

test("the scenes speak Spanish when given Spanish captions", () => {
  for (const [name, captions] of Object.entries(SPANISH)) assert.deepEqual(wordsOf(ArtScenes.scene(name, { captions })), Object.values(captions), name);
});

test("a missing caption is refused, naming the scene and the key", () => {
  const partial = Object.fromEntries(Object.entries(ENGLISH.timeline).filter(([key]) => key !== "snapshot"));
  assert.throws(() => ArtScenes.scene("timeline", { captions: partial }), (error) => error instanceof RangeError && /timeline/.test(error.message) && /snapshot/.test(error.message));
  assert.throws(() => ArtScenes.scene("chain"), (error) => error instanceof RangeError && /chain/.test(error.message) && /hash1/.test(error.message));
  assert.doesNotThrow(() => ArtScenes.scene("space"));
});

test("the moving pictures move with the art sheet's step animations", () => {
  const classes = (name) => [...walk(ArtScenes.scene(name, { captions: ENGLISH[name] }))].flatMap((node) => node.classList.list());
  const moves = { capsule: ["art-drop", "art-lid"], orbit: ["art-orbit"], rocket: ["art-push"], pull: ["art-pull"], alarm: ["art-alarm"], meteor: ["art-meteor", "art-boom", "art-alarm"], fork: ["art-slide"], collision: ["art-slide"], blackbox: ["art-vanish", "art-slide"], merge: ["art-pop"], simulator: ["art-belt", "art-pop"] };
  for (const [name, wanted] of Object.entries(moves)) for (const className of wanted) assert.ok(classes(name).includes(className), `${name} uses ${className}`);
});

test("an unknown scene is refused", () => {
  assert.throws(() => ArtScenes.scene("moon"), RangeError);
});

const fillsOf = (picture) => new Set([...walk(picture)].map((node) => node.getAttribute("fill")).filter(Boolean));

test("the alarm is a red beacon flashing on your station, with no meteorite and no explosion", () => {
  const alarm = ArtScenes.scene("alarm", { captions: ENGLISH.alarm });
  const classes = [...walk(alarm)].flatMap((node) => node.classList.list());
  assert.ok(!classes.includes("art-meteor") && !classes.includes("art-boom"));
  assert.ok(fillsOf(alarm).has("var(--art-violet)"), "your station's dome");
  const flashing = [...alarm.querySelectorAll("g.art-alarm rect")];
  assert.ok(flashing.length > 0 && flashing.every((rect) => rect.getAttribute("fill") === "var(--art-red)" && Number(rect.getAttribute("width")) <= 7), "a small red beacon that flashes");
});

test("the meteor strikes a dome under the base's label", () => {
  const meteor = ArtScenes.scene("meteor", { captions: ENGLISH.meteor });
  assert.ok(fillsOf(meteor).has("var(--art-hull)"), "the dome");
  assert.ok(meteor.querySelector(".art-meteor") && meteor.querySelector(".art-boom"));
});

test("the alarm and meteor domes have a pole that shows against the night", () => {
  for (const name of ["alarm", "meteor"]) {
    const dome = [...walk(ArtScenes.scene(name, { captions: ENGLISH[name] }))].find((node) => node.getAttribute("transform") === "translate(37 50) scale(3)");
    assert.ok(fillsOf(dome).has("var(--star)"), name);
  }
});

test("in the alarm, your base's label keeps clear of Rama", () => {
  const alarm = ArtScenes.scene("alarm", { captions: ENGLISH.alarm });
  const rama = [...walk(alarm)].find((node) => /^translate\(\d+ 38\) scale\(2\)$/.test(node.getAttribute("transform") || ""));
  const ramaLeft = Number(rama.getAttribute("transform").match(/translate\((\d+)/)[1]);
  assert.ok(ramaLeft >= 75, `Rama starts at ${ramaLeft}`);
});

test("the simulator feeds a belt of crates into the workshop, piled past its roof and falling outside", () => {
  const simulator = ArtScenes.scene("simulator", { captions: ENGLISH.simulator });
  const top = (node) => Number((node.getAttribute("transform") || "").match(/^translate\(\d+ (-?\d+)\)$/)?.[1]);
  const crates = [...simulator.querySelectorAll("g.art-pop")].map((pop) => pop.parentNode).filter((node) => !Number.isNaN(top(node)));
  const room = [...walk(simulator)].find((node) => node.getAttribute("data-part") === "workshop");
  const roof = Number(room.getAttribute("y"));
  const [left, right] = [Number(room.getAttribute("x")), Number(room.getAttribute("x")) + Number(room.getAttribute("width"))];
  const leftOf = (node) => Number(node.getAttribute("transform").match(/^translate\((\d+)/)[1]);
  assert.ok(crates.length >= 15, `${crates.length} crates`);
  assert.ok(crates.some((crate) => top(crate) < roof), "some crates stand above the roof");
  assert.ok(crates.some((crate) => leftOf(crate) < left || leftOf(crate) >= right), "some fall outside its walls");
  assert.ok(simulator.querySelectorAll(".art-belt").length >= 2, "crates ride the belt");
  assert.ok(fillsOf(simulator).has("var(--art-orange)"), "workshop crates in the workshop's colour");
});
