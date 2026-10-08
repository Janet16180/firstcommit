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

test("every plain icon is drawn in currentColor, 1em, hidden unless labelled", () => {
  assert.deepEqual(ArtSprites.ICONS, ["lock", "arrow", "back", "replay", "restart", "hint", "conflict", "merging", "inverted", "station-you", "station-alex"]);
  for (const name of ArtSprites.ICONS) {
    const icon = ArtSprites.icon(name);
    assert.equal(icon.getAttribute("height"), "1em");
    assert.ok(icon.classList.contains(`art-icon--${name}`));
    assert.ok(isHidden(icon));
    assertPalette(icon);
    assertStyled(icon);
    assert.equal(labelOf(ArtSprites.icon(name, { label: "Map" })), "Map");
  }
  for (const name of ["lock", "arrow", "back", "replay", "restart", "hint", "conflict", "merging"]) {
    const fills = new Set([...ArtSprites.icon(name).querySelectorAll("rect")].map((rect) => rect.getAttribute("fill")));
    assert.deepEqual(fills, new Set(["currentColor"]), name);
  }
  assert.equal(ArtSprites.icon("arrow").getAttribute("viewBox"), "0 0 8 7");
  assert.throws(() => ArtSprites.icon("rocket"), RangeError);
});

test("the conflict icon is a file with a crack running clean through it", () => {
  const conflict = ArtSprites.icon("conflict");
  const [, , width, height] = conflict.getAttribute("viewBox").split(" ").map(Number);
  const painted = new Set([...conflict.querySelectorAll("rect")].flatMap((rect) => {
    const x = Number(rect.getAttribute("x"));
    return Array.from({ length: Number(rect.getAttribute("width")) }, (_, step) => `${x + step},${rect.getAttribute("y")}`);
  }));
  const gaps = Array.from({ length: height }, (_, y) => Array.from({ length: width }, (_cell, x) => x).filter((x) => x > 0 && x < width - 1 && !painted.has(`${x},${y}`)));
  assert.ok(gaps[0].length > 0 && gaps[height - 1].length > 0, "the crack breaks the top and bottom edges");
  assert.ok(gaps.every((row) => row.length > 0), "and every row between");
});

test("the paused merge marker has two arrows meeting at a pause bar that blinks", () => {
  const merging = ArtSprites.icon("merging");
  const bars = merging.querySelectorAll("rect.art-pause");
  assert.ok(bars.length >= 2);
  assert.ok(merging.querySelectorAll("rect:not(.art-pause)").length >= 6);
});

test("the inverted capsule is a block outlined and shaded in tokens, its body in the zone's colour", () => {
  const inverted = ArtSprites.icon("inverted");
  const fills = new Set([...inverted.querySelectorAll("rect")].map((rect) => rect.getAttribute("fill")));
  assert.ok(fills.has("currentColor") && fills.has("var(--edge)"));
  assert.equal(inverted.getAttribute("viewBox"), "0 0 9 9");
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

test("each crew station is a dome with a flag in that crew member's colours, Alex's matching their capsule", () => {
  const fills = (name) => new Set([...ArtSprites.icon(name).querySelectorAll("rect")].map((rect) => rect.getAttribute("fill")));
  assert.ok(fills("station-you").has("var(--art-violet)") && !fills("station-you").has("var(--art-pink)"));
  assert.ok(fills("station-alex").has("var(--art-pink)") && !fills("station-alex").has("var(--art-violet)"));
  assert.ok(fills("station-alex").has("var(--art-yellow)"), "the flag");
  assert.equal(labelOf(ArtSprites.icon("station-alex", { label: "Alex's station" })), "Alex's station");
});
