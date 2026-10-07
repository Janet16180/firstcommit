"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const { html } = require("./fakedom");
const { installBrowser, load } = require("./load");
const { assertPalette, assertStyled, isHidden } = require("./art-check");

installBrowser();
const { ArtSky } = load(["dom.js", "art-pixels.js", "art-sky.js"], ["ArtSky"]);

test("a sector's star field fills a 200x60 strip, the same for a seed and different for another", () => {
  const field = ArtSky.field("sector-1");
  assert.equal(field.getAttribute("viewBox"), "0 0 200 60");
  assert.equal(field.getAttribute("preserveAspectRatio"), "xMidYMid slice");
  assert.equal(field.querySelectorAll("rect").length, 46);
  assert.equal(html(field), html(ArtSky.field("sector-1")));
  assert.notEqual(html(field), html(ArtSky.field("sector-2")));
  assert.ok(isHidden(field));
  assertPalette(field);
  assertStyled(field);
});

test("the background dust is specks in --speck spread over the window, some twinkling", () => {
  const dust = ArtSky.dust(1);
  const specks = dust.querySelectorAll("rect");
  assert.equal(specks.length, 70);
  assert.ok([...specks].every((speck) => speck.getAttribute("fill") === "var(--speck)" && /%$/.test(speck.getAttribute("x"))));
  assert.ok(dust.querySelector(".art-tw"));
  assert.equal(html(dust), html(ArtSky.dust(1)));
  assert.ok(isHidden(dust));
  assertPalette(dust);
  assertStyled(dust);
});

test("the celebration burst is 32 squares in five colours and three sizes, each with its own path", () => {
  const burst = ArtSky.sparks();
  const sparks = burst.querySelectorAll(".art-spark");
  assert.equal(sparks.length, 32);
  const style = (spark, name) => spark.getAttribute("style").match(new RegExp(`${name}:([^;]+)`))[1];
  assert.equal(new Set([...sparks].map((spark) => style(spark, "background"))).size, 5);
  assert.deepEqual(new Set([...sparks].map((spark) => style(spark, "--size"))), new Set(["6px", "8px", "12px"]));
  assert.equal(new Set([...sparks].map((spark) => `${style(spark, "--dx")} ${style(spark, "--dy")} ${style(spark, "--far")}`)).size, 32);
  assert.equal(burst.getAttribute("aria-hidden"), "true");
  assert.equal(html(burst), html(ArtSky.sparks()));
  assertPalette(burst);
  assertStyled(burst);
});
