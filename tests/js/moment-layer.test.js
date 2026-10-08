"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { createClock, installBrowser, load } = require("./load");
const { labelOf } = require("./art-check");

installBrowser();
const { MomentLayer, ArtMoments, Strings, Dom } = load(["dom.js", "strings.js", "art-pixels.js", "art-moments.js", "moment-layer.js"], ["MomentLayer", "ArtMoments", "Strings", "Dom"]);

/* Plays with a stand-in for ArtMoments.play, whose moments end when the test says. */
async function withFakeMoments(run) {
  const real = ArtMoments.play;
  const played = [];
  ArtMoments.play = (name, options) => {
    let end;
    const finished = new Promise((resolve) => (end = resolve));
    const element = Dom.svg("svg", { class: "art-moment" });
    played.push({ name, options, end });
    return { element, finished };
  };
  try {
    return await run(played);
  } finally {
    ArtMoments.play = real;
  }
}

test("every moment plays in both languages, its captions and the what-if heading from the page's strings", () => {
  for (const language of ["en", "es"]) {
    Strings.use(language);
    for (const name of ArtMoments.NAMES) {
      const layer = MomentLayer.create({ timers: createClock() });
      layer.play(name);
      assert.equal(labelOf(layer.element.querySelector(".art-moment")), Strings.t(`moment.${name}.caption`), `${language} ${name}`);
    }
  }
  Strings.use("es");
  const layer = MomentLayer.create({ timers: createClock() });
  layer.play("force-break");
  assert.ok([...layer.element.querySelectorAll("text")].some((node) => node.textContent === "¿Y SI…?"));
  Strings.use("en");
});

test("a moment covers the zones until it is over", async () => {
  await withFakeMoments(async (played) => {
    const layer = MomentLayer.create();
    assert.equal(layer.element.hidden, true);
    assert.equal(layer.showing(), false);
    layer.play("launch");
    assert.equal(layer.element.hidden, false);
    assert.equal(layer.showing(), true);
    assert.ok(Boolean(layer.element.querySelector(".art-moment")));
    played[0].end();
    await new Promise((resolve) => setImmediate(resolve));
    assert.equal(layer.element.hidden, true);
    assert.equal(layer.showing(), false);
    assert.equal(layer.element.childNodes.length, 0);
  });
});

test("a click puts the moment away before it is over", async () => {
  await withFakeMoments(() => {
    const layer = MomentLayer.create();
    layer.play("secret-leak");
    layer.element.click();
    assert.equal(layer.element.hidden, true);
  });
});

test("each moment plays once while the layer lives", async () => {
  await withFakeMoments((played) => {
    const layer = MomentLayer.create();
    layer.play("secret-leak");
    layer.play("secret-leak");
    layer.play("launch");
    assert.deepEqual(played.map((moment) => moment.name), ["secret-leak", "launch"]);
  });
});

test("when the player asked for reduced motion the moment is told so, and shows its still frame", async () => {
  await withFakeMoments((played) => {
    MomentLayer.create({ reducedMotion: true }).play("launch");
    MomentLayer.create({ reducedMotion: false }).play("launch");
    assert.deepEqual(played.map((moment) => moment.options.reducedMotion), [true, false]);
  });
});

test("the layer says when no moment is showing: at once, or once the moment is over or put away", async () => {
  await withFakeMoments(async (played) => {
    const layer = MomentLayer.create();
    let idle = false;
    await layer.idle();
    layer.play("launch");
    layer.idle().then(() => (idle = true));
    await new Promise((resolve) => setImmediate(resolve));
    assert.equal(idle, false);
    played[0].end();
    await new Promise((resolve) => setImmediate(resolve));
    assert.equal(idle, true);

    let away = false;
    layer.play("secret-leak");
    layer.idle().then(() => (away = true));
    layer.element.click();
    await new Promise((resolve) => setImmediate(resolve));
    assert.equal(away, true);
  });
});
