"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { html } = require("./fakedom");
const { installBrowser, load } = require("./load");
const { assertPalette } = require("./art-check");

installBrowser();
const { ArtPixels, Dom } = load(["dom.js", "art-pixels.js"], ["ArtPixels", "Dom"]);

test("a grid becomes one rect per run of a colour, and clear pixels draw nothing", () => {
  const rects = ArtPixels.draw(["aab.", ".a.b"], { a: "var(--gold)", b: "var(--ink)" });
  const runs = rects.map((rect) => ["x", "y", "width", "fill"].map((name) => rect.getAttribute(name)).join(" "));
  assert.deepEqual(runs, ["0 0 2 var(--gold)", "2 0 1 var(--ink)", "1 1 1 var(--gold)", "3 1 1 var(--ink)"]);
});

test("a palette entry may be a set of attributes", () => {
  const [rect] = ArtPixels.draw(["d"], { d: { fill: "currentColor", "fill-opacity": "0.45" } });
  assert.equal(rect.getAttribute("fill-opacity"), "0.45");
});

test("a picture with a label is an image with that name; without one it is hidden", () => {
  const named = ArtPixels.picture({ viewBox: "0 0 1 1" }, "Rama", []);
  assert.equal(named.getAttribute("role"), "img");
  assert.equal(named.getAttribute("aria-label"), "Rama");
  const plain = ArtPixels.picture({ viewBox: "0 0 1 1" }, "", []);
  assert.equal(plain.getAttribute("aria-hidden"), "true");
  assert.equal(plain.hasAttribute("role"), false);
});

test("the same seed gives the same numbers, another seed others, all in [0, 1)", () => {
  const take = (seed) => Array.from({ length: 50 }, ArtPixels.random(seed));
  assert.deepEqual(take("sector-1"), take("sector-1"));
  assert.notDeepEqual(take("sector-1"), take("sector-2"));
  assert.ok(take(7).every((value) => value >= 0 && value < 1));
});

test("stars stay inside their grid, use the star tokens and come out the same for a seed", () => {
  const options = { count: 40, width: 20, height: 10, twinkle: 0.3, tint: 0.25, dim: 0.6 };
  const field = ArtPixels.stars(3, options);
  assert.equal(field.length, 40);
  for (const star of field) {
    assert.ok(Number(star.getAttribute("x")) < 20 && Number(star.getAttribute("y")) < 10);
    assert.match(star.getAttribute("fill"), /^var\(--(star|crt-hint)\)$/);
  }
  assert.ok(field.some((star) => star.classList.contains("art-tw")), "some stars twinkle");
  assert.equal(field.map(html).join(""), ArtPixels.stars(3, options).map(html).join(""));
});

test("Rama has a body, blinking eyes and a flickering flame, in tokens only", () => {
  const group = Dom.svg("g", {}, ArtPixels.rama());
  assert.ok(group.querySelector(".art-eyes rect"));
  assert.ok(group.querySelector(".art-flick rect"));
  assertPalette(group);
});

test("a planet fits its reported size, and only a palette with a ring draws one", () => {
  const plain = ArtPixels.planet(14, { a: "var(--art-orange)", b: "var(--art-orange-dk)", c: "var(--art-orange-lt)" });
  assert.deepEqual([plain.width, plain.height], [31, 31]);
  const ringed = ArtPixels.planet(11, { a: "var(--art-cyan)", b: "var(--art-cyan-dk)", c: "var(--art-cyan-lt)", n: "var(--art-hull)" });
  assert.ok(ringed.width > ringed.height, "a ring is wider than its planet");
  for (const { rects, width, height } of [plain, ringed]) {
    for (const rect of rects) {
      assert.ok(Number(rect.getAttribute("x")) + Number(rect.getAttribute("width")) <= width);
      assert.ok(Number(rect.getAttribute("y")) < height);
    }
  }
  assert.ok(ringed.rects.some((rect) => rect.getAttribute("fill") === "var(--art-hull)"));
  assert.ok(!plain.rects.some((rect) => rect.getAttribute("fill") === "var(--art-hull)"));
});
