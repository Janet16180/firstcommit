"use strict";

/*
 * The page's small pictures: Rama, the rating stars, the pixel icons and the sector planets.
 * Defines one global, ArtSprites; dom.js and art-pixels.js load first, art-style.css styles them.
 * Every function returns a new <svg> (stars() a <span> of three). A `label` option names a
 * picture that carries meaning; without one the picture is decorative and aria-hidden.
 *
 * rama({size, label})     size "header" (84x94, bobs), "comms" (52x58) or "here" (32x36, bobs).
 * star(on, {label, pop, delay})
 *                         gold with a hard shadow when on, --s-clean when off; 1em square, so
 *                         it takes the font size. `pop` plays the design's pop-in after `delay` s.
 * stars(earned, {label, pop})
 *                         a row of three stars named "<earned> of 3 stars" unless `label` says
 *                         otherwise; with `pop` the earned ones pop in one after another.
 * icon(name, {label})     one of ICONS, drawn in currentColor, 1em. art-style.css gives three a
 *                         default colour: "conflict" (a cracked file) --s-new, "merging" (two
 *                         arrows meeting at a blinking pause bar) --s-mod, and "inverted" (a
 *                         .cblock turned over, outlined in --edge) the zone's --zc.
 *                         "station-you" and "station-alex" are a crew member's base dome and
 *                         flag, in ArtPixels.CREW colours (violet, and pink like Alex's capsule).
 * planet(index, {label})  the planet of the sector at 0-based `index`: orange, cyan with a ring,
 *                         violet, pink with a ring, then again. Square; the page sets its size.
 */

/* global Dom, ArtPixels */
/* exported ArtSprites */

const ArtSprites = (function () {
  const { tone, draw, picture, rama: ramaParts, planet: planetParts, ARROW, shape, CREW } = ArtPixels;

  const RAMA_SIZES = { header: [84, 94], comms: [52, 58], here: [32, 36] };

  function rama({ size = "header", label = "" } = {}) {
    if (!(size in RAMA_SIZES)) throw new RangeError(`unknown Rama size: ${size}`);
    const [width, height] = RAMA_SIZES[size];
    return picture({ class: `art-sprite art-rama art-rama--${size}`, viewBox: "0 0 16 18", width, height }, label, ramaParts());
  }

  const STAR = [
    "....s....",
    "...sss...",
    "...sss...",
    "sssssssss",
    ".sssssss.",
    "..sssss..",
    "..sssss..",
    ".sss.sss.",
    ".ss...ss.",
  ];

  function star(on, { label = "", pop = false, delay = 0 } = {}) {
    const drawn = on
      ? [Dom.svg("g", { transform: "translate(1 1)" }, draw(STAR, { s: tone("edge") })), draw(STAR, { s: tone("gold") })]
      : draw(STAR, { s: tone("s-clean") });
    const popping = on && pop;
    const className = ["art-star", on ? "art-star--on" : "art-star--off", popping && "art-pop"].filter(Boolean).join(" ");
    return picture({ class: className, viewBox: "0 0 10 10", width: "1em", height: "1em", style: popping ? `animation-delay:${delay}s` : null }, label, drawn);
  }

  function stars(earned, { label = "", pop = false } = {}) {
    if (!Number.isInteger(earned) || earned < 0 || earned > 3) throw new RangeError(`stars must be 0 to 3, not ${earned}`);
    const row = [0, 1, 2].map((index) => star(index < earned, { pop, delay: (0.35 + index * 0.18).toFixed(2) }));
    return Dom.el("span", { class: "art-stars", role: "img", "aria-label": label || `${earned} of 3 stars` }, row);
  }

  const INK = "currentColor";
  const FAINT = { fill: INK, "fill-opacity": "0.45" };
  const PLAIN = { c: INK, d: FAINT };
  const plain = (rows) => [[rows, PLAIN]];

  function station(colours) {
    const { rows, palette } = shape("station", colours);
    return [[rows, palette]];
  }

  /* Each icon is layers of [rows, palette], drawn in order. */
  const ICONS = {
    lock: plain(["..ccc..", ".c...c.", ".c...c.", "ccccccc", "cddcddc", "cddcddc", "cdddddc", "ccccccc"]),
    arrow: plain(ARROW.map((row) => row.replaceAll("k", "c"))),
    back: plain(["....cc..", "...cc...", "..cc....", ".cc.....", "..cc....", "...cc...", "....cc.."]),
    replay: plain(["ccccccccc", "c.......c", "c..c....c", "c..cc...c", "c..ccc..c", "c..cc...c", "c..c....c", "ccccccccc"]),
    restart: plain(["...ccc.c.", ".cc...cc.", ".c...ccc.", "c........", "c.......c", "c.......c", ".c.....c.", ".cc...cc.", "...ccc..."]),
    hint: plain(["..ccc..", ".cdddc.", "cdddddc", "cdddddc", ".cdddc.", "..cdc..", "..ccc..", "..ccc..", "...c..."]),
    /* A dog-eared sheet split top to bottom by a jagged gap. */
    conflict: plain([
      "cccc.cc..",
      "cccc.cdc.",
      "ccc.ccddc",
      "ccc.ccccc",
      "cccc.cccc",
      "ccccc.ccc",
      "ccccc.ccc",
      "cccc.cccc",
      "ccc.ccccc",
      "ccc.ccccc",
    ]),
    /* Two arrows meeting at a pause bar (p), which blinks. */
    merging: [[[
      "......p.p......",
      "......p.p......",
      "..c...p.p...c..",
      "..cc..p.p..cc..",
      "ccccc.p.p.ccccc",
      "..cc..p.p..cc..",
      "..c...p.p...c..",
      "......p.p......",
      "......p.p......",
    ], { c: INK, p: { fill: INK, class: "art-pause" } }]],
    /* A capsule block (.cblock) turned over: its shade on the top and left instead of the bottom
       and right, and a pale chevron pointing down. */
    inverted: [
      [["kkkkkkkkk", "kbbbbbbbk", "kbbbbbbbk", "kbbbbbbbk", "kbbbbbbbk", "kbbbbbbbk", "kbbbbbbbk", "kbbbbbbbk", "kkkkkkkkk"], { k: tone("edge"), b: INK }],
      [[".........", ".sssssss.", ".sssssss.", ".ss......", ".ss......", ".ss......", ".ss......", ".ss......"], { s: { fill: tone("edge"), "fill-opacity": "0.3" } }],
      [["", "", "", "...h...h", "....h.h.", ".....h.."], { h: tone("panel") }],
    ],
    "station-you": station(CREW.you),
    "station-alex": station(CREW.alex),
  };

  function icon(name, { label = "" } = {}) {
    if (!(name in ICONS)) throw new RangeError(`unknown icon: ${name}`);
    const layers = ICONS[name];
    const [rows] = layers[0];
    const width = Math.max(...rows.map((row) => row.length));
    const shapes = layers.map(([layerRows, palette]) => draw(layerRows, palette));
    return picture({ class: `art-icon art-icon--${name}`, viewBox: `0 0 ${width} ${rows.length}`, width: "1em", height: "1em" }, label, shapes);
  }

  const PLANETS = [
    { radius: 14, palette: { a: tone("art-orange"), b: tone("art-orange-dk"), c: tone("art-orange-lt") } },
    { radius: 11, palette: { a: tone("art-cyan"), b: tone("art-cyan-dk"), c: tone("art-cyan-lt"), n: tone("art-hull") } },
    { radius: 14, palette: { a: tone("art-violet"), b: tone("art-violet-dk"), c: tone("art-violet-lt") } },
    { radius: 11, palette: { a: tone("art-pink"), b: tone("art-pink-dk"), c: tone("art-pink-lt"), n: tone("art-yellow") } },
  ];

  function planet(index, { label = "" } = {}) {
    if (!Number.isInteger(index) || index < 0) throw new RangeError(`a sector index is a whole number from 0, not ${index}`);
    const { radius, palette } = PLANETS[index % PLANETS.length];
    const { rects, width, height } = planetParts(radius, palette);
    const side = Math.max(width, height);
    const viewBox = `${-(side - width) / 2} ${-(side - height) / 2} ${side} ${side}`;
    return picture({ class: "art-planet", viewBox }, label, rects);
  }

  return { rama, star, stars, icon, planet, ICONS: Object.keys(ICONS), RAMA_SIZES: Object.keys(RAMA_SIZES) };
})();
