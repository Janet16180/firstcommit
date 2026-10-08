"use strict";

/*
 * One-time moments that play over the level screen's zones, on a 400x100 night canvas that fills
 * its layer (letterboxed). Defines one global, ArtMoments; dom.js and art-pixels.js load first,
 * art-style.css animates them. Every part is drawn where it stands in the moment's still frame;
 * the animations, timed by --art-moment, play the states before and after it.
 *
 * NAMES                   "launch" (4-2b: the two halves of the ship join and it launches), which
 *                         is real, and the what-ifs, which play in greyscale under the `whatIf`
 *                         heading, then rewind, and never show the real state changed:
 *                         "secret-leak" (2-3: the keys reach every crew station), "junk-flood"
 *                         (2-5: `git add .` sends the build crates to every station),
 *                         "unreviewed-main" (5-5: your capsule lands on main at Alex's),
 *                         "force-break" (6-4, 7-2: your capsule replaces Alex's on the mothership,
 *                         which cracks and falls) and "search-beam" (7-1: a beam sweeps the black
 *                         box, the workshop outside it, and finds nothing).
 * CAPTIONS                {moment: [key, ...]}: the captions each moment draws, in drawing order.
 * play(name, {captions, reducedMotion, timers})
 *                         {element, finished}: a new <svg> named by captions.caption, and a promise
 *                         that resolves when the moment is over (also when still, so the caption
 *                         can be read), timed on `timers` (window unless given). A missing caption
 *                         is a RangeError.
 */

/* global Dom, ArtPixels */
/* exported ArtMoments */

const ArtMoments = (function () {
  const { tone, draw, place, text, picture, stars, sprite, CREW, NIGHT_POLE } = ArtPixels;

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
  const station = (x, colours) => place(x, GROUND - 16, 2, sprite("station", { ...colours, ...NIGHT_POLE }));

  /* A capsule 24x16 at (x, y), its cargo glyph inside. */
  const capsuleAt = (x, y, recolour = {}) => place(x, y, 2, sprite("capsule", recolour));
  const KEY = ["rrr....", "r.rrrrr", "rrr.r.r"];
  const MINI_CRATE = ["kkkkk", "kbbbk", "kbbbk", "kkkkk"];
  /* The key is starlight: the what-ifs are greyscale, and it must stand out on the capsule. */
  const keyCapsule = (x, y) => [capsuleAt(x, y), place(x + 9, y + 7, 1, draw(KEY, { r: tone("star") }))];
  const crateCapsule = (x, y) => [capsuleAt(x, y), place(x + 10, y + 6, 1, draw(MINI_CRATE, { k: tone("art-outline"), b: tone("art-cyan") }))];
  const MUTED_CAPSULE = { v: tone("art-muted"), V: tone("art-muted-dk"), h: tone("art-hull") };
  const ALEX_CAPSULE = { v: CREW.alex.a, V: CREW.alex.b, h: CREW.alex.c };
  /* The 4x2 link from a capsule at (x, y) back to the one before it. */
  const linkBefore = (x, y) => rect(x - 4, y + 7, 4, 2, tone("star"));

  /* The "WHAT IF" heading in the top left corner. */
  function heading(words) {
    const width = Math.ceil(words.length * 9 * 0.42) + 10;
    return [rect(6, 5, width, 13, tone("crt"), { stroke: tone("star"), "stroke-width": 1 }), text(11, 14.5, words, { size: 9, anchor: "start" })];
  }

  const OTHER_CREW = [
    { a: tone("art-cyan"), b: tone("art-cyan-dk"), c: tone("art-cyan-lt") },
    { a: tone("art-orange"), b: tone("art-orange-dk"), c: tone("art-orange-lt") },
    { a: tone("art-yellow"), b: tone("art-yellow-dk"), c: tone("art-flame-hot") },
    { a: tone("art-muted"), b: tone("art-muted-dk"), c: tone("art-hull") },
  ];

  /* Where a commit leaves from (above the dock's crate), docks under the mothership, and the four
     crew stations its copies land at. */
  const STAGING = { x: 60, y: 36 };
  const DOCK = { x: 178, y: 24 };
  const CREW_STATIONS = [236, 278, 320, 362];
  const mothership = () => place(168, 4, 2, sprite("ship"));

  /* The ghost capsule, drawn docked, rising there from (from.x, from.y) and back. */
  const rising = (moving, from, at, children) => part(moving, "art-wi-rise", children, offset(from.x - at.x, from.y - at.y));

  /* A copy drawn landed at (x, y), coming down from the dock and going back up. */
  const landing = (moving, x, y, children) => part(moving, "art-wi-land", children, offset(DOCK.x - x, DOCK.y - y));

  /* Copies of a capsule with `cargo` inside, landed above the four crew stations. */
  const crewCopies = (moving, cargo, glow) => CREW_STATIONS.map((x, index) => [
    station(x, OTHER_CREW[index]),
    landing(moving, x - 1, 36, [
      cargo(x - 1, 36),
      glow && part(moving, "art-wi-glow", part(moving, "art-alarm", rect(x - 3, 34, 28, 20, "none", { stroke: tone("art-red"), "stroke-width": 1 }))),
    ]),
  ]);

  function secretLeak(c, moving) {
    return [
      backdrop("secret-leak"),
      heading(c.whatIf),
      station(22, CREW.you),
      place(STAGING.x, GROUND - 20, 2, sprite("crate")),
      moving && part(moving, "art-wi-sweep", place(64, 30, 2, sprite("file", { p: tone("art-red-lt") })), offset(0, 0)),
      mothership(),
      rising(moving, STAGING, DOCK, [
        Dom.svg("g", { opacity: 0.6 }, keyCapsule(DOCK.x, DOCK.y)),
        text(DOCK.x + 28, DOCK.y + 11, c.keys, { fill: tone("art-red-lt"), anchor: "start" }),
      ]),
      text(162, 14, c.mothership, { fill: tone("art-pink"), anchor: "end" }),
      crewCopies(moving, keyCapsule, true),
      captionBand(c.caption, moving, "art-wi-caption"),
    ];
  }

  function junkFlood(c, moving) {
    const pile = [[0, 10], [16, 10], [8, 0]];
    return [
      backdrop("junk-flood"),
      heading(c.whatIf),
      rect(6, 34, 38, 38, "none", { stroke: tone("art-orange"), "stroke-width": 1 }),
      text(25, 30, c.command, { size: 8 }),
      moving && part(moving, "art-wi-sweep", pile.map(([dx, dy]) => place(STAGING.x + 2 + dx, 30 + dy, 1, sprite("crate"))), offset(-52, 20)),
      place(STAGING.x, GROUND - 20, 2, sprite("crate")),
      mothership(),
      rising(moving, STAGING, DOCK, Dom.svg("g", { opacity: 0.6 }, crateCapsule(DOCK.x, DOCK.y))),
      crewCopies(moving, crateCapsule, false),
      captionBand(c.caption, moving, "art-wi-caption"),
    ];
  }

  /* The mothership with its main line: two capsules, and the place a third would dock. */
  const MAIN = [120, 148];
  const mainLine = () => [mothership(), MAIN.map((x, index) => [capsuleAt(x, 26, MUTED_CAPSULE), index > 0 && linkBefore(x, 26)])];
  /* Your capsule waiting above your station. */
  const YOUR_CAPSULE = { x: 23, y: 38 };

  function unreviewedMain(c, moving) {
    const end = { x: 176, y: 26 };
    return [
      backdrop("unreviewed-main"),
      heading(c.whatIf),
      station(24, CREW.you),
      mainLine(),
      rising(moving, YOUR_CAPSULE, end, [linkBefore(end.x, end.y), capsuleAt(end.x, end.y)]),
      station(352, CREW.alex),
      part(moving, "art-wi-land", capsuleAt(351, 38), offset(end.x - 351, end.y - 38)),
      captionBand(c.caption, moving, "art-wi-caption"),
    ];
  }

  function forceBreak(c, moving) {
    const line = { x: 176, y: 26 };
    const fallen = { x: 184, y: 58 };
    const falling = moving ? { class: "art-wi-fall", style: offset(line.x - fallen.x, line.y - fallen.y) } : {};
    return [
      backdrop("force-break"),
      heading(c.whatIf),
      station(24, CREW.you),
      text(36, 30, c.command, { size: 8 }),
      mothership(),
      capsuleAt(148, 26, MUTED_CAPSULE),
      Dom.svg("g", { opacity: 0.7, ...falling }, [
        linkBefore(fallen.x, fallen.y),
        capsuleAt(fallen.x, fallen.y, ALEX_CAPSULE),
        /* Starlight, not red: the what-if is greyscale and the crack must still show. */
        part(moving, "art-wi-crack", place(fallen.x + 8, fallen.y + 3, 1.3, sprite("crack", { c: tone("star") }))),
      ]),
      rising(moving, YOUR_CAPSULE, line, [linkBefore(line.x, line.y), capsuleAt(line.x, line.y)]),
      station(352, CREW.alex),
      captionBand(c.caption, moving, "art-wi-caption"),
    ];
  }

  function searchBeam(c, moving) {
    const dissolving = [[22, 40], [50, 46], [30, 62], [46, 58]];
    return [
      backdrop("search-beam"),
      heading(c.whatIf),
      rect(8, 30, 56, 42, "none", { stroke: tone("art-orange"), "stroke-width": 1 }),
      Dom.svg("g", { opacity: 0.25 }, place(28, 40, 2, sprite("file"))),
      dissolving.map(([x, y]) => rect(x, y, 2, 2, tone("star"), { opacity: 0.4 })),
      rect(84, 8, 306, 64, "none", { stroke: tone("art-orange"), "stroke-width": 2 }),
      [[84, 8], [386, 8], [84, 68], [386, 68]].map(([x, y]) => rect(x, y, 4, 4, tone("art-orange-dk"))),
      place(104, 46, 2, sprite("crate")),
      capsuleAt(170, 48),
      linkBefore(198, 48),
      capsuleAt(198, 48),
      place(300, 20, 2, sprite("ship")),
      moving && part(moving, "art-wi-beam", [rect(88, 10, 10, 60, tone("art-yellow"), { opacity: 0.3 }), rect(97, 10, 1, 60, tone("art-flame-hot"))]),
      part(moving, "art-wi-mark", place(230, 32, 2, sprite("cross", { k: tone("star") }))),
      captionBand(c.caption, moving, "art-wi-caption"),
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
    "secret-leak": { captions: ["whatIf", "keys", "mothership", "caption"], seconds: 7, whatIf: true, draw: secretLeak },
    launch: { captions: ["nav", "engine", "caption"], seconds: 5, whatIf: false, draw: launch },
    "junk-flood": { captions: ["whatIf", "command", "caption"], seconds: 7, whatIf: true, draw: junkFlood },
    "unreviewed-main": { captions: ["whatIf", "caption"], seconds: 7, whatIf: true, draw: unreviewedMain },
    "force-break": { captions: ["whatIf", "command", "caption"], seconds: 7, whatIf: true, draw: forceBreak },
    "search-beam": { captions: ["whatIf", "caption"], seconds: 7, whatIf: true, draw: searchBeam },
  };

  const NAMES = Object.freeze(Object.keys(MOMENTS));
  const CAPTIONS = Object.freeze(Object.fromEntries(NAMES.map((name) => [name, Object.freeze([...MOMENTS[name].captions])])));

  function play(name, { captions = {}, reducedMotion = false, timers = window } = {}) {
    if (!(name in MOMENTS)) throw new RangeError(`unknown moment: ${name}`);
    const missing = CAPTIONS[name].find((key) => typeof captions[key] !== "string");
    if (missing) throw new RangeError(`the ${name} moment needs the caption "${missing}"`);
    const { seconds, whatIf, draw: parts } = MOMENTS[name];
    const element = picture({
      class: ["art-moment", `art-moment--${name}`, whatIf && "art-moment--whatif"].filter(Boolean).join(" "),
      viewBox: `0 0 ${WIDTH} ${HEIGHT}`,
      width: "100%",
      height: "100%",
      preserveAspectRatio: "xMidYMid meet",
      style: `--art-moment:${seconds}s`,
    }, captions.caption, parts(captions, !reducedMotion));
    const finished = new Promise((resolve) => timers.setTimeout(resolve, seconds * 1000));
    return { element, finished };
  }

  return { NAMES, CAPTIONS, play };
})();
