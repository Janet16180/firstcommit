"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { installBrowser, load } = require("./load");
const { assertPalette, assertStyled, isHidden, labelOf } = require("./art-check");

installBrowser();
const { ArtSprites } = load(["dom.js", "art-pixels.js", "art-sprites.js"], ["ArtSprites"]);

test("Rama comes in the header, comms and map-marker sizes, on his 16x18 grid", () => {
  const sizes = { header: ["84", "94"], comms: ["52", "58"], here: ["32", "36"] };
  for (const [size, box] of Object.entries(sizes)) {
    const rama = ArtSprites.rama({ size });
    assert.equal(rama.getAttribute("viewBox"), "0 0 16 18");
    assert.deepEqual([rama.getAttribute("width"), rama.getAttribute("height")], box);
    assert.ok(rama.classList.contains(`art-rama--${size}`));
    assert.ok(rama.querySelector(".art-eyes") && rama.querySelector(".art-flick"));
    assert.ok(isHidden(rama), "decorative by default");
    assertPalette(rama);
    assertStyled(rama);
  }
});

test("Rama takes a label, and an unknown size is refused", () => {
  assert.equal(labelOf(ArtSprites.rama({ size: "comms", label: "Rama" })), "Rama");
  assert.throws(() => ArtSprites.rama({ size: "huge" }), RangeError);
});

test("a star on is gold over a hard shadow; off, it is muted with no shadow", () => {
  const on = ArtSprites.star(true);
  const fills = (node) => new Set(node.querySelectorAll("rect").length ? [...node.querySelectorAll("rect")].map((rect) => rect.getAttribute("fill")) : []);
  assert.deepEqual(fills(on), new Set(["var(--edge)", "var(--gold)"]));
  assert.deepEqual(fills(ArtSprites.star(false)), new Set(["var(--s-clean)"]));
  assert.equal(on.getAttribute("width"), "1em");
  for (const star of [on, ArtSprites.star(false)]) {
    assertPalette(star);
    assertStyled(star);
  }
});

test("a row of stars is named by what was earned, its stars hidden, and earned ones pop in turn", () => {
  const row = ArtSprites.stars(2, { pop: true });
  assert.equal(labelOf(row), "2 of 3 stars");
  const stars = row.querySelectorAll("svg");
  assert.equal(stars.length, 3);
  assert.deepEqual([...stars].map((star) => star.classList.contains("art-star--on")), [true, true, false]);
  assert.ok([...stars].every(isHidden));
  assert.deepEqual([...stars].map((star) => star.classList.contains("art-pop")), [true, true, false]);
  assert.notEqual(stars[0].getAttribute("style"), stars[1].getAttribute("style"));
  assert.equal(labelOf(ArtSprites.stars(0, { label: "No stars yet" })), "No stars yet");
  assert.throws(() => ArtSprites.stars(4), RangeError);
});

test("every icon is drawn in currentColor, 1em, hidden unless labelled", () => {
  assert.deepEqual(ArtSprites.ICONS, ["lock", "arrow", "back", "replay", "restart", "hint"]);
  for (const name of ArtSprites.ICONS) {
    const icon = ArtSprites.icon(name);
    const fills = new Set([...icon.querySelectorAll("rect")].map((rect) => rect.getAttribute("fill")));
    assert.deepEqual(fills, new Set(["currentColor"]), name);
    assert.equal(icon.getAttribute("height"), "1em");
    assert.ok(isHidden(icon));
    assertStyled(icon);
    assert.equal(labelOf(ArtSprites.icon(name, { label: "Map" })), "Map");
  }
  assert.equal(ArtSprites.icon("arrow").getAttribute("viewBox"), "0 0 8 7");
  assert.throws(() => ArtSprites.icon("rocket"), RangeError);
});

test("the sector planets cycle orange, ringed cyan, violet, ringed pink, in a square box", () => {
  const main = (index) => ArtSprites.planet(index).querySelector("rect[fill^=\"var(--art-\"]:not([fill=\"var(--art-outline)\"])");
  const colours = [0, 1, 2, 3, 4, 7].map((index) => {
    const fills = [...ArtSprites.planet(index).querySelectorAll("rect")].map((rect) => rect.getAttribute("fill"));
    return ["orange", "cyan", "violet", "pink"].find((name) => fills.includes(`var(--art-${name})`));
  });
  assert.deepEqual(colours, ["orange", "cyan", "violet", "pink", "orange", "pink"]);
  assert.ok(main(0));
  for (const index of [0, 1, 2, 3]) {
    const planet = ArtSprites.planet(index);
    const [, , width, height] = planet.getAttribute("viewBox").split(" ").map(Number);
    assert.equal(width, height);
    assertPalette(planet);
    assertStyled(planet);
  }
  assert.equal(labelOf(ArtSprites.planet(0, { label: "Sector 1" })), "Sector 1");
  assert.throws(() => ArtSprites.planet(-1), RangeError);
});
