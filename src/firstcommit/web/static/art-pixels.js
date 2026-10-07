"use strict";

/*
 * The pixel-art toolkit the other art-* scripts draw with. Defines one global, ArtPixels; dom.js
 * loads first. Pictures are inline SVG built from character grids, as in the approved design
 * (docs/drafts/orbit-design.html): each character is one pixel, '.' (or any character missing
 * from the palette) is clear, and runs of one colour become one <rect>.
 *
 * tone(name)                    "var(--name)": every colour is a token of app.css or art-style.css.
 * draw(rows, palette)           the grid's <rect>s; a palette value is a fill or an attribute object.
 * place(x, y, scale, children, {className, delay})
 *                               a group moved and scaled, its animation (a class) on an inner group
 *                               so CSS transforms do not replace the placement.
 * picture(attributes, label, children)
 *                               an <svg>: with a label it is an image with that name, without one it
 *                               is hidden from assistive technology.
 * random(seed)                  a deterministic generator of numbers in [0, 1) for a number or text seed.
 * stars(seed, {count, width, height, twinkle, tint, dim})
 *                               1x1 stars scattered over a width x height grid.
 * rama()                        Rama's body, blinking eyes and flickering flame, on a 16x18 grid.
 * planet(radius, palette)       a round pixel planet, with a ring when the palette has `n`;
 *                               returns {rects, width, height}.
 * ARROW                         the 8x7 flow arrow, pointing right.
 */

/* global Dom */
/* exported ArtPixels */

const ArtPixels = (function () {
  const tone = (name) => `var(--${name})`;

  function draw(rows, palette) {
    const rects = [];
    rows.forEach((row, y) => {
      let x = 0;
      while (x < row.length) {
        let run = 1;
        while (row[x + run] === row[x]) run += 1;
        const paint = palette[row[x]];
        if (paint) rects.push(Dom.svg("rect", { x, y, width: run, height: 1, ...(typeof paint === "string" ? { fill: paint } : paint) }));
        x += run;
      }
    });
    return rects;
  }

  function place(x, y, scale, children, { className = null, delay = null } = {}) {
    const transform = scale === 1 ? `translate(${x} ${y})` : `translate(${x} ${y}) scale(${scale})`;
    const timing = delay === null ? null : `animation-delay:${delay}s`;
    return Dom.svg("g", { transform }, Dom.svg("g", { class: className, style: timing }, children));
  }

  function picture(attributes, label, children) {
    const access = label ? { role: "img", "aria-label": label } : { "aria-hidden": "true", focusable: "false" };
    return Dom.svg("svg", { ...attributes, "shape-rendering": "crispEdges", ...access }, children);
  }

  /* FNV-1a turns the seed into 32 bits; mulberry32 walks from there. */
  function random(seed) {
    let state = 2166136261;
    for (const character of String(seed)) state = Math.imul(state ^ character.codePointAt(0), 16777619);
    return () => {
      state = (state + 0x6d2b79f5) | 0;
      let mixed = Math.imul(state ^ (state >>> 15), 1 | state);
      mixed = (mixed + Math.imul(mixed ^ (mixed >>> 7), 61 | mixed)) ^ mixed;
      return ((mixed ^ (mixed >>> 14)) >>> 0) / 4294967296;
    };
  }

  function stars(seed, { count, width, height, twinkle, tint, dim }) {
    const next = random(seed);
    const pick = (top) => Math.floor(next() * top);
    return Array.from({ length: count }, () => {
      const x = pick(width);
      const y = pick(height);
      const fill = next() < tint ? tone("crt-hint") : tone("star");
      const twinkles = next() < twinkle;
      const delay = (next() * 2).toFixed(2);
      return Dom.svg("rect", { x, y, width: 1, height: 1, fill, opacity: twinkles ? 1 : dim, class: twinkles && "art-tw", style: twinkles && `animation-delay:${delay}s` });
    });
  }

  const RAMA_BODY = [
    ".......gg.......",
    ".......ss.......",
    "...kkkkkkkkkk...",
    "..kwwwwwwwwwwk..",
    ".kwvvvvvvvvvvwk.",
    ".kwvvvvvvvvvvwk.",
    ".kwvvvvvvvvvvwk.",
    ".kwvvvvvvvvvvwk.",
    ".kswwwwwwwwwwsk.",
    "..kssssssssssk..",
    "...kkkwwwwkkk...",
    "..kwwwwppwwwwk..",
    "kkswwwwwwwwwwskk",
    "..kwwwwwwwwwwk..",
    "...kssssssssk...",
    "....kkkkkkkk....",
  ];
  const RAMA_EYES = ["", "", "", "", "", ".....cc..cc.....", ".....cc..cc....."];
  const RAMA_FLAME = [...Array(16).fill(""), "......oyyo......", ".......oo......."];
  const RAMA_TONES = { k: tone("art-outline"), w: tone("art-hull"), s: tone("art-hull-shade"), v: tone("void-2"), g: tone("art-yellow"), p: tone("art-pink") };

  const rama = () => [
    draw(RAMA_BODY, RAMA_TONES),
    Dom.svg("g", { class: "art-eyes" }, draw(RAMA_EYES, { c: tone("art-mint") })),
    Dom.svg("g", { class: "art-flick" }, draw(RAMA_FLAME, { o: tone("art-orange"), y: tone("art-flame-hot") })),
  ];

  /* A disc with a dark rim, a light spot up and to the left, shade down and to the right, and an
     optional flat ring drawn in front of the lower half and beside the disc. */
  function planet(radius, palette) {
    const ringed = "n" in palette;
    const halfWidth = ringed ? Math.round(radius * 1.75) : radius + 1;
    const width = halfWidth * 2 + 1;
    const height = radius * 2 + 3;
    const rows = Array.from({ length: height }, (_, row) =>
      Array.from({ length: width }, (_cell, column) => planetPixel(column - halfWidth, row - (radius + 1), radius, ringed && halfWidth)).join(""));
    return { rects: draw(rows, { k: tone("art-outline"), ...palette }), width, height };
  }

  /* The pixel at (x, y) from the planet's centre: rim k, spot c, shade b, body a, ring n, or clear. */
  function planetPixel(x, y, radius, ringHalfWidth) {
    const inside = (dx, dy) => dx * dx + dy * dy <= radius * radius + radius * 0.6;
    if (ringHalfWidth && onRing(x, y, radius, ringHalfWidth) && (y >= 0 || !inside(x, y))) return "n";
    if (!inside(x, y)) return ".";
    if (!inside(x + 1, y) || !inside(x - 1, y) || !inside(x, y + 1) || !inside(x, y - 1)) return "k";
    const spotX = x + radius * 0.38;
    const spotY = y + radius * 0.38;
    if (spotX * spotX + spotY * spotY < (radius * 0.3) ** 2) return "c";
    return x + y > radius * 0.55 ? "b" : "a";
  }

  function onRing(x, y, radius, halfWidth) {
    const distance = (x * x) / (halfWidth * halfWidth) + (y * y) / (radius * 0.42) ** 2;
    return distance > 0.72 && distance < 1.18;
  }

  const ARROW = ["....k...", "....kk..", "kkkkkkk.", "kkkkkkkk", "kkkkkkk.", "....kk..", "....k..."];

  return { tone, draw, place, picture, random, stars, rama, planet, ARROW };
})();
