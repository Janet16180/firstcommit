"use strict";

/*
 * The level scenes: the pictures beside Rama's short explanation the first time a level opens,
 * on the design's 160x90 night canvas, with its animations. Defines one global, ArtScenes;
 * dom.js and art-pixels.js load first, art-style.css animates them.
 *
 * NAMES                   the scenes there are, the values of the engine's `Art`.
 * scene(name, {label})    a new <svg> of that scene, named by `label` or by the scene's own
 *                         description; it scales to its box (the page sets the width).
 */

/* global Dom, ArtPixels */
/* exported ArtScenes */

const ArtScenes = (function () {
  const { tone, draw, place, picture, stars, rama: ramaParts, planet, ARROW } = ArtPixels;
  const OUTLINE = tone("art-outline");

  const FOLDER = {
    rows: ["kkkkkk........", "kyyyyyk.......", "kyyyyyykkkkkkk", "kyyyyyyyyyyyyk", "kddddddddddddk", "kyyyyyyyyyyyyk", "kyyyyyyyyyyyyk", "kyyyyyyyyyyyyk", "kddddddddddddk", "kkkkkkkkkkkkkk"],
    palette: { k: OUTLINE, y: tone("art-yellow"), d: tone("art-yellow-dk") },
  };
  const CRATE = {
    rows: ["kkkkkkkkkkkk", "kbbbbbbbbbbk", "kbkkkkkkkkbk", "kbkbbbbbbkbk", "kbkbBBBBbkbk", "kbkbbbbbbkbk", "kbkkkkkkkkbk", "kbbbbbbbbbbk", "kBBBBBBBBBBk", "kkkkkkkkkkkk"],
    palette: { k: OUTLINE, b: tone("art-cyan"), B: tone("art-cyan-dk") },
  };
  const CAPSULE = {
    rows: ["..kkkkkkkk..", ".kvhhvvvvvk.", "kvhvvvvvvvvk", "kvvvvvvvvvvk", "kvvvvvvvvvvk", "kVvvvvvvvvVk", ".kVVVVVVVVk.", "..kkkkkkkk.."],
    palette: { k: OUTLINE, v: tone("art-violet"), V: tone("art-violet-dk"), h: tone("art-violet-lt") },
  };
  const FLAG = {
    rows: ["kkkkkkk..", "krrrrrrk.", "krrwwrrrk", "krrrrrrk.", "kkkkkkk.."],
    palette: { k: OUTLINE, r: tone("art-pink"), w: tone("star") },
  };
  const CROSS = { rows: ["kk...kk", ".kk.kk.", "..kkk..", ".kk.kk.", "kk...kk"], palette: { k: tone("art-red") } };
  const FILE_ROWS = ["kkkkkk..", "kppppkk.", "kppppkpk", "kppppppk", "kplllppk", "kppppppk", "kplllllk", "kppppppk", "kpllllpk", "kkkkkkkk"];

  const sprite = ({ rows, palette }) => draw(rows, palette);
  const file = (paper = "star") => draw(FILE_ROWS, { k: OUTLINE, p: tone(paper), l: tone("crt-soft") });
  const arrow = () => draw(ARROW, { k: tone("star") });
  const ramaAt = (x, y) => place(x, y, 2, Dom.svg("g", { class: "art-bob" }, ramaParts()));
  const sky = (name, count) => stars(name, { count, width: 160, height: 71, twinkle: 0.3, tint: 0.25, dim: 0.6 });
  const rect = (x, y, width, height, fill, extra = {}) => Dom.svg("rect", { x, y, width, height, fill, ...extra });

  function text(x, y, words, { fill = tone("star"), size = 8, anchor = "middle", className = null, delay = null } = {}) {
    const classes = ["art-text", className].filter(Boolean).join(" ");
    return Dom.svg("text", { x, y, "text-anchor": anchor, "font-size": size, fill, class: classes, style: delay === null ? null : `animation-delay:${delay}s` }, words);
  }

  const timed = (className, delay, children) => Dom.svg("g", { class: className, style: `animation-delay:${delay}s` }, children);

  const ground = () => [
    rect(0, 74, 160, 16, tone("art-ground")),
    rect(0, 74, 160, 1, tone("art-ground-edge")),
    rect(18, 79, 10, 2, tone("art-ground-pit")),
    rect(20, 78, 6, 1, tone("art-ground-pit")),
    rect(118, 82, 14, 2, tone("art-ground-pit")),
    rect(121, 81, 8, 1, tone("art-ground-pit")),
  ];

  function planetAt(x, y, radius, palette) {
    const { rects, width, height } = planet(radius, palette);
    return place(x - Math.floor(width / 2), y - Math.floor(height / 2), 1, rects);
  }

  /* The top half of a small cyan planet, a dome standing on the ground. */
  function dome(x, y) {
    const { rects, width } = planet(9, { a: tone("art-cyan"), b: tone("art-cyan-dk"), c: tone("art-cyan-lt") });
    return [
      Dom.svg("svg", { x: x - 9, y: y - 10, width, height: 11, viewBox: `0 0 ${width} 11`, overflow: "hidden" }, rects),
      rect(x - 10, y, 21, 2, OUTLINE),
    ];
  }

  const ZONE_TONES = ["art-orange", "art-cyan", "art-violet", "art-pink"];

  const SCENES = {
    space: {
      label: "Rama hovers above a small base with a flag, a ringed planet in the sky",
      draw: () => [
        sky("space", 55),
        planetAt(132, 20, 9, { a: tone("art-pink"), b: tone("art-pink-dk"), c: tone("art-pink-lt"), n: tone("art-violet") }),
        ground(),
        dome(108, 74),
        rect(108, 54, 1, 10, tone("star")),
        place(109, 54, 1, sprite(FLAG), { className: "art-wave" }),
        ramaAt(30, 34),
      ],
    },
    timeline: {
      label: "Four snapshots, v1 to v4, and an arrow back to the first: every commit is a snapshot",
      draw: () => [
        sky("timeline", 25),
        [0, 1, 2, 3].map((index) => {
          const left = 22 + index * 32;
          return timed("art-pop", index * 0.45, [
            rect(left, 38, 22, 26, tone("art-hull"), { stroke: OUTLINE, "stroke-width": 1 }),
            rect(left + 3, 41, 16, 13, tone(ZONE_TONES[index])),
            rect(left + 5, 49, 4, 3, OUTLINE),
            rect(left + 11, 46, 5, 6, OUTLINE, { opacity: 0.6 }),
            text(left + 11, 62, `v${index + 1}`, { fill: OUTLINE }),
          ]);
        }),
        timed("art-fade", 2.1, [
          rect(129, 24, 2, 12, tone("art-pink")),
          rect(33, 24, 98, 2, tone("art-pink")),
          rect(33, 24, 2, 10, tone("art-pink")),
          rect(30, 32, 8, 2, tone("art-pink")),
          rect(32, 34, 4, 2, tone("art-pink")),
        ]),
        text(82, 18, "back in time", { fill: tone("art-pink"), size: 9, className: "art-fade", delay: 2.4 }),
        text(80, 80, "every commit is a snapshot", { size: 9, className: "art-fade", delay: 1.6 }),
      ],
    },
    terminal: {
      label: "A terminal: ls lists the folder, then git status fails because the folder is not a Git repository",
      draw: () => [
        sky("terminal", 25),
        rect(8, 14, 112, 60, tone("crt"), { stroke: tone("star"), "stroke-width": 1 }),
        rect(9, 15, 110, 7, tone("crt-2")),
        rect(16, 17, 3, 3, tone("art-pink")),
        rect(21, 17, 3, 3, tone("art-yellow")),
        rect(26, 17, 3, 3, tone("art-cyan")),
        text(17, 32, "$ ls", { fill: tone("crt-cmd"), size: 9, anchor: "start", className: "art-fade", delay: 0.4 }),
        timed("art-fade", 1, [
          rect(17, 36, 22, 3, tone("crt-ink"), { opacity: 0.75 }),
          rect(45, 36, 28, 3, tone("crt-ink"), { opacity: 0.75 }),
          rect(79, 36, 16, 3, tone("crt-ink"), { opacity: 0.75 }),
        ]),
        text(17, 53, "$ git status", { fill: tone("crt-cmd"), size: 9, anchor: "start", className: "art-fade", delay: 1.8 }),
        text(17, 62, "fatal: not a git repository", { fill: tone("crt-err"), size: 7, anchor: "start", className: "art-fade", delay: 2.4 }),
        rect(17, 65, 4, 6, tone("crt-cmd"), { class: "art-alarm" }),
        ramaAt(128, 36),
      ],
    },
    planet: {
      label: "A plain folder on a planet, in a dashed outline: does Git know it?",
      draw: () => [
        sky("planet", 35),
        ground(),
        place(73, 54, 2, sprite(FOLDER)),
        rect(62, 46, 50, 30, "none", { stroke: tone("art-muted"), "stroke-width": 1, "stroke-dasharray": "3 3" }),
        text(87, 22, "a plain folder", { size: 9 }),
        text(87, 38, "does Git know it?", { fill: tone("art-muted") }),
        ramaAt(14, 36),
      ],
    },
    flag: {
      label: "git init plants a flag beside the folder and creates .git",
      draw: () => [
        sky("flag", 35),
        ground(),
        place(56, 54, 2, sprite(FOLDER)),
        timed("art-rise", 0.2, [rect(96, 40, 2, 34, tone("star")), place(98, 40, 2, sprite(FLAG), { className: "art-wave" })]),
        text(108, 32, "git init", { fill: tone("art-yellow"), size: 10, className: "art-fade", delay: 0.9 }),
        timed("art-pop", 1.5, [rect(122, 56, 26, 14, tone("crt"), { stroke: tone("art-mint"), "stroke-width": 1 }), text(135, 66, ".git", { fill: tone("art-mint"), size: 10 })]),
        rect(122, 56, 26, 14, "none", { stroke: tone("art-mint"), "stroke-width": 1, class: "art-ring", style: "animation-delay:1.9s" }),
        ramaAt(10, 36),
      ],
    },
    zones: {
      label: "Three zones: the workshop where you edit, the cargo dock where you pick, the vault where you keep",
      draw: () => [
        sky("zones", 20),
        [
          ["workshop", "art-orange", "you edit", place(22, 30, 2, file())],
          ["cargo dock", "art-cyan", "you pick", place(70, 32, 2, sprite(CRATE))],
          ["vault", "art-violet", "you keep", place(122, 32, 2, sprite(CAPSULE))],
        ].map(([name, colour, doing, cargo], index) => timed("art-pop", index * 0.5, [
          rect(12 + index * 52, 22, 36, 36, tone("void-2"), { stroke: tone(colour), "stroke-width": 2 }),
          cargo,
          text(30 + index * 52, 70, name, { fill: tone(colour), size: 9 }),
          text(30 + index * 52, 80, doing, { fill: tone("art-muted") }),
        ])),
        [0, 1].map((index) => place(50 + index * 52, 37, 1, arrow(), { className: "art-fade", delay: 0.4 + index * 0.5 })),
      ],
    },
    conveyor: {
      label: "git add picks what goes up: two files hop from the workshop belt to the cargo dock, a third is left behind",
      draw: () => [
        sky("conveyor", 20),
        rect(8, 58, 64, 5, tone("art-orange"), { stroke: OUTLINE, "stroke-width": 1 }),
        rect(12, 63, 3, 14, tone("art-muted-dk")),
        rect(64, 63, 3, 14, tone("art-muted-dk")),
        text(40, 86, "workshop", { fill: tone("art-orange"), size: 9 }),
        place(104, 46, 3, sprite(CRATE)),
        text(122, 86, "cargo dock", { fill: tone("art-cyan"), size: 9 }),
        Dom.svg("g", { class: "art-hop-a" }, place(14, 38, 2, file())),
        Dom.svg("g", { class: "art-hop-b" }, place(32, 38, 2, file())),
        Dom.svg("g", { class: "art-shake" }, place(50, 38, 2, file("art-red-lt"))),
        place(52, 26, 1, sprite(CROSS), { className: "art-pop", delay: 2.2 }),
        text(80, 14, "git add picks what goes up", { size: 10 }),
      ],
    },
  };

  const NAMES = Object.freeze(Object.keys(SCENES));

  function scene(name, { label = "" } = {}) {
    if (!(name in SCENES)) throw new RangeError(`unknown scene: ${name}`);
    const { label: description, draw: parts } = SCENES[name];
    const backdrop = rect(0, 0, 160, 90, tone("void"));
    return picture({ class: "art-scene", viewBox: "0 0 160 90", "data-scene": name }, label || description, [backdrop, parts()]);
  }

  return { NAMES, scene };
})();
