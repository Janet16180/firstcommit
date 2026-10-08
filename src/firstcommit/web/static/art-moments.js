"use strict";

/*
 * One-time moments that play over the level screen's zones, on a 400x100 night canvas that fills
 * its layer (letterboxed). Defines one global, ArtMoments; dom.js and art-pixels.js load first,
 * art-style.css animates them. Every part is drawn where it stands in the moment's still frame;
 * the animations, timed by --art-moment, play the states before and after it.
 *
 * NAMES                   "secret-leak" (2-3: the keys sealed in a commit reach every crew
 *                         station, then it rewinds) and "launch" (4-2b: the two halves of the ship
 *                         join and it launches).
 * CAPTIONS                {moment: [key, ...]}: the captions each moment draws, in drawing order.
 * play(name, {captions, reducedMotion})
 *                         {element, finished}: a new <svg> named by captions.caption, and a promise
 *                         that resolves when the moment is over (also when still, so the caption
 *                         can be read). A missing caption is a RangeError.
 */

/* global Dom, ArtPixels */
/* exported ArtMoments */

const ArtMoments = (function () {
  const { tone, draw, place, text, picture, stars, sprite, CREW } = ArtPixels;

  const WIDTH = 400;
  const HEIGHT = 100;
  const GROUND = 72;
  const BAND = 78;
  const CAPTION_SIZE = 9;
  /* VT323 draws a character about 0.42 of its size wide. */
  const CAPTION_CHARACTERS = Math.floor((WIDTH - 20) / (CAPTION_SIZE * 0.42));

  const rect = (x, y, width, height, fill, extra = {}) => Dom.svg("rect", { x, y, width, height, fill, ...extra });

  /* A group that plays `className` when the moment moves, and is a plain group in the still frame. */
  const part = (moving, className, children, style = null) => Dom.svg("g", moving ? { class: className, style } : {}, children);
  const offset = (dx, dy) => `--dx:${dx}px;--dy:${dy}px`;

  /* The caption on one line, or two split at the space nearest the middle when it is too long. */
  function captionLines(words) {
    if (words.length <= CAPTION_CHARACTERS) return [words];
    const middle = words.length / 2;
    const spaces = [...words.matchAll(/ /g)].map((match) => match.index);
    const cut = spaces.reduce((best, index) => (Math.abs(index - middle) < Math.abs(best - middle) ? index : best), spaces[0]);
    return [words.slice(0, cut), words.slice(cut + 1)];
  }

  function captionBand(words, moving, className) {
    const lines = captionLines(words);
    const top = lines.length === 1 ? 93 : 88;
    return [
      rect(0, BAND, WIDTH, HEIGHT - BAND, tone("crt")),
      rect(0, BAND, WIDTH, 1, tone("art-ground-edge")),
      part(moving, className, lines.map((line, index) => text(WIDTH / 2, top + index * 9, line, { size: CAPTION_SIZE }))),
    ];
  }

  const backdrop = (seed) => [
    rect(0, 0, WIDTH, HEIGHT, tone("void")),
    stars(seed, { count: 60, width: WIDTH, height: GROUND, twinkle: 0.3, tint: 0.25, dim: 0.6 }),
    rect(0, GROUND, WIDTH, BAND - GROUND, tone("art-ground")),
    rect(0, GROUND, WIDTH, 1, tone("art-ground-edge")),
  ];

  /* A crew station, its dome 22x16 standing on the ground with its left edge at x. */
  const station = (x, colours) => place(x, GROUND - 16, 2, sprite("station", colours));

  const KEY = ["rrr....", "r.rrrrr", "rrr.r.r"];
  const keyAt = (x, y) => place(x, y, 1, draw(KEY, { r: tone("art-red") }));

  /* A capsule 24x16 at (x, y) with the keys inside. */
  const keyCapsule = (x, y) => [place(x, y, 2, sprite("capsule")), keyAt(x + 9, y + 7)];

  const OTHER_CREW = [
    { a: tone("art-cyan"), b: tone("art-cyan-dk"), c: tone("art-cyan-lt") },
    { a: tone("art-orange"), b: tone("art-orange-dk"), c: tone("art-orange-lt") },
    { a: tone("art-yellow"), b: tone("art-yellow-dk"), c: tone("art-flame-hot") },
    { a: tone("art-muted"), b: tone("art-muted-dk"), c: tone("art-hull") },
  ];

  function secretLeak(c, moving) {
    const staging = { x: 60, y: 36 };
    const dock = { x: 178, y: 24 };
    const home = offset(staging.x - dock.x, staging.y - dock.y);
    const crew = [236, 278, 320, 362];
    return [
      backdrop("secret-leak"),
      station(22, CREW.you),
      place(60, GROUND - 20, 2, sprite("crate")),
      moving && part(moving, "art-leak-file", place(64, 30, 2, sprite("file", { p: tone("art-red-lt") }))),
      place(168, 4, 2, sprite("ship")),
      text(162, 14, c.mothership, { fill: tone("art-pink"), anchor: "end" }),
      part(moving, "art-leak-ghost", [
        Dom.svg("g", { opacity: 0.6 }, keyCapsule(dock.x, dock.y)),
        text(dock.x + 28, dock.y + 11, c.keys, { fill: tone("art-red-lt"), anchor: "start" }),
      ], home),
      crew.map((x, index) => [
        station(x, OTHER_CREW[index]),
        part(moving, "art-leak-copy", [
          keyCapsule(x - 1, 36),
          part(moving, "art-leak-glow", part(moving, "art-alarm", rect(x - 3, 34, 28, 20, "none", { stroke: tone("art-red"), "stroke-width": 1 }))),
        ], offset(dock.x - (x - 1), dock.y - 36)),
      ]),
      captionBand(c.caption, moving, "art-leak-caption"),
    ];
  }

  const NAV = [
    ".....kk.....",
    "....kwwk....",
    "...kwwwwk...",
    "...kwwwwk...",
    "..kwwccwwk..",
    "..kwcmmcwk..",
    "..kwwccwwk..",
    "..kwwwwwwk..",
    "..kwwwwwwk..",
    "..kppppppk..",
  ];
  const ENGINE = [
    "..kwwwwwwk..",
    "..kwwwwwwk..",
    "..kwwwwwwk..",
    ".kkwwwwwwkk.",
    "kffkwwwwkffk",
    "kffkwwwwkffk",
    "kfkkkkkkkkfk",
    "kk..kggk..kk",
    "....kggk....",
  ];
  const FLAME = ["....oyyo....", ".....oo.....", ".....yy....."];
  const HULL = { k: tone("art-outline"), w: tone("art-hull"), c: tone("art-cyan"), m: tone("art-mint"), g: tone("art-muted-dk") };

  function launch(c, moving) {
    const ship = { x: 182, nav: 6, engine: 36 };
    const yours = { x: 53, y: GROUND - 16 - 30 };
    const alexs = { x: 311, y: GROUND - 16 - 27 };
    return [
      backdrop("launch"),
      station(60, CREW.you),
      station(318, CREW.alex),
      part(moving, "art-launch-ship", [
        part(moving, "art-launch-join", [
          place(ship.x, ship.nav, 3, draw(NAV, { ...HULL, p: CREW.you.a })),
          text(ship.x - 2, ship.nav + 19, c.nav, { fill: tone("art-violet-lt"), anchor: "end" }),
        ], offset(yours.x - ship.x, yours.y - ship.nav)),
        part(moving, "art-launch-join", [
          place(ship.x, ship.engine, 3, draw(ENGINE, { ...HULL, f: CREW.alex.a })),
          text(ship.x - 2, ship.engine + 16, c.engine, { fill: tone("art-pink-lt"), anchor: "end" }),
        ], offset(alexs.x - ship.x, alexs.y - ship.engine)),
        part(moving, "art-launch-flame", place(ship.x, ship.engine + 27, 3, part(moving, "art-flick", draw(FLAME, { o: tone("art-orange"), y: tone("art-flame-hot") })))),
      ]),
      moving && part(moving, "art-launch-ring", rect(ship.x - 4, ship.nav - 3, 44, 64, "none", { stroke: tone("art-mint"), "stroke-width": 1 })),
      captionBand(c.caption, moving, "art-launch-caption"),
    ];
  }

  const MOMENTS = {
    "secret-leak": { captions: ["keys", "mothership", "caption"], seconds: 7, draw: secretLeak },
    launch: { captions: ["nav", "engine", "caption"], seconds: 5, draw: launch },
  };

  const NAMES = Object.freeze(Object.keys(MOMENTS));
  const CAPTIONS = Object.freeze(Object.fromEntries(NAMES.map((name) => [name, Object.freeze([...MOMENTS[name].captions])])));

  function play(name, { captions = {}, reducedMotion = false } = {}) {
    if (!(name in MOMENTS)) throw new RangeError(`unknown moment: ${name}`);
    const missing = CAPTIONS[name].find((key) => typeof captions[key] !== "string");
    if (missing) throw new RangeError(`the ${name} moment needs the caption "${missing}"`);
    const { seconds, draw: parts } = MOMENTS[name];
    const element = picture({
      class: `art-moment art-moment--${name}`,
      viewBox: `0 0 ${WIDTH} ${HEIGHT}`,
      width: "100%",
      height: "100%",
      preserveAspectRatio: "xMidYMid meet",
      style: `--art-moment:${seconds}s`,
    }, captions.caption, parts(captions, !reducedMotion));
    const finished = new Promise((resolve) => setTimeout(resolve, seconds * 1000));
    return { element, finished };
  }

  return { NAMES, CAPTIONS, play };
})();
